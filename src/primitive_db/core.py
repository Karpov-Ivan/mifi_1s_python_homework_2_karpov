from primitive_db.utils import load_table_data

SUPPORTED_TYPES = {"int", "str", "bool"}


def create_table(metadata: dict, table_name: str, columns: list[str]) -> dict:
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata
    if not table_name.isidentifier() or not columns:
        print(f"Некорректное значение: {table_name}. Попробуйте снова.")
        return metadata

    schema = [{"name": "ID", "type": "int"}]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        name, data_type = parts
        if (
            not name.isidentifier()
            or data_type not in SUPPORTED_TYPES
            or name in names
            or (name == "ID" and data_type != "int")
        ):
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        names.add(name)
        if name != "ID":
            schema.append({"name": name, "type": data_type})

    metadata[table_name] = schema
    description = ", ".join(f"{c['name']}:{c['type']}" for c in schema)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {description}')
    return metadata


def drop_table(metadata: dict, table_name: str) -> dict:
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata: dict) -> None:
    if not metadata:
        print("Таблиц пока нет.")
        return
    for table_name in metadata:
        print(f"- {table_name}")


PYTHON_TYPES = {"int": int, "str": str, "bool": bool}


def get_schema(metadata: dict, table_name: str) -> list[dict]:
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    schema = metadata[table_name]
    if (
        not isinstance(schema, list)
        or not schema
        or schema[0] != {"name": "ID", "type": "int"}
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
    types = {column["name"]: column["type"] for column in schema}
    for name, value in clause.items():
        if name not in types:
            raise ValueError(f"Столбец {name} не существует.")
        if updating and name == "ID":
            raise ValueError("ID генерируется автоматически и не изменяется.")
        if type(value) is not PYTHON_TYPES[types[name]]:
            raise ValueError(
                f"Некорректное значение для {name}: ожидается {types[name]}."
            )


def validate_table_data(schema: list[dict], table_data: list[dict]) -> None:
    names = {column["name"] for column in schema}
    ids = set()
    for row in table_data:
        if set(row) != names:
            raise ValueError("Данные записи не соответствуют столбцам таблицы.")
        validate_clause(schema, row)
        if row["ID"] < 1 or row["ID"] in ids:
            raise ValueError("ID записей должны быть положительными и уникальными.")
        ids.add(row["ID"])


def insert(metadata: dict, table_name: str, values: list) -> list[dict]:
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
    row["ID"] = max((record["ID"] for record in table_data), default=0) + 1
    return [*table_data, row]


def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    if where_clause is None:
        return table_data[:]
    return [
        row
        for row in table_data
        if all(row.get(name) == value for name, value in where_clause.items())
    ]


def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    matches = select(table_data, where_clause)
    return [
        dict(row, **set_clause) if row in matches else row.copy() for row in table_data
    ]


def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    matches = select(table_data, where_clause)
    return [row for row in table_data if row not in matches]
