import json
import os

from primitive_db.constants import (
    DATA_DIR,
    JSON_ENCODING,
    JSON_INDENT,
    TEMP_TOKEN_BYTES,
)


def load_metadata(filepath: str) -> dict:
    """Загружает метаданные из JSON или возвращает пустой словарь."""
    try:
        with open(filepath, encoding=JSON_ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Метаданные должны быть JSON-объектом.")
    return data


def save_metadata(filepath: str, data: dict) -> None:
    """Сохраняет метаданные в JSON через атомарную замену файла."""
    save_json(filepath, data)


def table_path(table_name: str) -> str:
    """Возвращает путь к JSON-файлу таблицы с проверенным именем."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name: str) -> list[dict]:
    """Загружает записи таблицы или возвращает пустой список."""
    try:
        with open(table_path(table_name), encoding=JSON_ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError(f"Некорректные данные таблицы {table_name}.")
    return data


def save_table_data(table_name: str, data: list[dict]) -> None:
    """Сохраняет записи таблицы в её JSON-файл."""
    save_json(table_path(table_name), data)


def delete_table_data(table_name: str) -> None:
    """Удаляет файл данных таблицы, если он существует."""
    try:
        os.remove(table_path(table_name))
    except FileNotFoundError:
        pass


def save_json(filepath: str, data) -> None:
    """Записывает JSON во временный файл и заменяет целевой файл."""
    filepath = os.fspath(filepath)
    parent = os.path.dirname(filepath) or "."
    os.makedirs(parent, exist_ok=True)
    temporary = os.path.join(
        parent,
        f".{os.path.basename(filepath)}.{os.urandom(TEMP_TOKEN_BYTES).hex()}.tmp",
    )
    created = False
    try:
        with open(temporary, "x", encoding=JSON_ENCODING) as file:
            created = True
            json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)
            file.write("\n")
        os.replace(temporary, filepath)
    finally:
        if created and os.path.exists(temporary):
            os.remove(temporary)
