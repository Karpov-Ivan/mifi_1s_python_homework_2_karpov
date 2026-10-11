import json

from primitive_db.constants import ID_COLUMN, ID_TYPE, PYTHON_TYPES, SUPPORTED_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data

_select_cache = create_cacher()


@handle_db_errors
def create_table(metadata: dict, table_name: str, columns: list[str]) -> dict:
    """Проверяет схему и добавляет таблицу с автоматическим столбцом ID."""
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    if not table_name.isidentifier() or not columns:
        raise ValueError(f"Некорректное значение: {table_name}. Попробуйте снова.")

    schema = [{"name": ID_COLUMN, "type": ID_TYPE}]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        name, data_type = parts
        if (
            not name.isidentifier()
            or data_type not in SUPPORTED_TYPES
            or name in names
            or (name == ID_COLUMN and data_type != ID_TYPE)
        ):
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        names.add(name)
        if name != ID_COLUMN:
            schema.append({"name": name, "type": data_type})

    metadata[table_name] = schema
    description = ", ".join(f"{c['name']}:{c['type']}" for c in schema)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {description}')
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> dict:
    """Удаляет таблицу из метаданных после подтверждения пользователя."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


@handle_db_errors
def list_tables(metadata: dict) -> None:
    """Выводит имена всех таблиц или сообщение об их отсутствии."""
    if not metadata:
        print("Таблиц пока нет.")
        return
    for table_name in metadata:
        print(f"- {table_name}")


def get_schema(metadata: dict, table_name: str) -> list[dict]:
    """Возвращает проверенную схему существующей таблицы."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    schema = metadata[table_name]
    if (
        not isinstance(schema, list)
        or not schema
        or schema[0] != {"name": ID_COLUMN, "type": ID_TYPE}
        or any(
            not isinstance(column, dict)
            or not isinstance(column.get("name"), str)
            or not column["name"].isidentifier()
            or not isinstance(column.get("type"), str)
            or column["type"] not in PYTHON_TYPES
            for column in schema
        )
        or len({column["name"] for column in schema}) != len(schema)
    ):
        raise ValueError(f'Некорректная схема таблицы "{table_name}".')
    return schema


def validate_clause(schema: list[dict], clause: dict, *, updating: bool = False):
    """Проверяет имена столбцов, типы значений и запрет изменения ID."""
    types = {column["name"]: column["type"] for column in schema}
    for name, value in clause.items():
        if name not in types:
            raise ValueError(f"Столбец {name} не существует.")
        if updating and name == ID_COLUMN:
            raise ValueError("ID генерируется автоматически и не изменяется.")
        if type(value) is not PYTHON_TYPES[types[name]]:
            raise ValueError(
                f"Некорректное значение для {name}: ожидается {types[name]}."
            )


def validate_table_data(schema: list[dict], table_data: list[dict]) -> None:
    """Проверяет структуру записей, типы полей и уникальность ID."""
    names = {column["name"] for column in schema}
    ids = set()
    for row in table_data:
        if set(row) != names:
            raise ValueError("Данные записи не соответствуют столбцам таблицы.")
        validate_clause(schema, row)
        if row[ID_COLUMN] < 1 or row[ID_COLUMN] in ids:
            raise ValueError("ID записей должны быть положительными и уникальными.")
        ids.add(row[ID_COLUMN])


@handle_db_errors
@log_time
def insert(metadata: dict, table_name: str, values: list) -> list[dict]:
    """Добавляет запись с новым ID и возвращает обновлённые данные таблицы."""
    schema = get_schema(metadata, table_name)
    columns = schema[1:]
    if len(values) != len(columns):
        raise ValueError(
            f"Ожидается {len(columns)} значений без ID, получено {len(values)}."
        )
    row = {column["name"]: value for column, value in zip(columns, values)}
    validate_clause(schema, row)
    table_data = load_table_data(table_name)
    validate_table_data(schema, table_data)
    row[ID_COLUMN] = max((record[ID_COLUMN] for record in table_data), default=0) + 1
    return [*table_data, row]


@handle_db_errors
@log_time
def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    """Возвращает записи по условию, используя кэш для одинаковых запросов."""
    key = (
        json.dumps(table_data, sort_keys=True, ensure_ascii=False),
        json.dumps(where_clause, sort_keys=True, ensure_ascii=False),
    )
    return _select_cache(
        key,
        lambda: [row for row in table_data if matches(row, where_clause)],
    )


def matches(row: dict, where_clause: dict | None) -> bool:
    """Проверяет соответствие записи условию с учётом типов значений."""
    if where_clause is None:
        return True
    return all(
        type(row.get(name)) is type(value) and row.get(name) == value
        for name, value in where_clause.items()
    )


@handle_db_errors
def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    """Возвращает копии записей с изменениями для подходящих строк."""
    if ID_COLUMN in set_clause:
        raise ValueError("ID генерируется автоматически и не изменяется.")
    return [
        dict(row, **set_clause) if matches(row, where_clause) else row.copy()
        for row in table_data
    ]


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    """Возвращает данные без подходящих записей после подтверждения."""
    return [row for row in table_data if not matches(row, where_clause)]
