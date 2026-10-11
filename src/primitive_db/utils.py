import json
import os
import tempfile
from pathlib import Path


def load_metadata(filepath: str) -> dict:
    try:
        with open(filepath, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Метаданные должны быть JSON-объектом.")
    return data


def save_metadata(filepath: str, data: dict) -> None:
    save_json(Path(filepath), data)


def table_path(table_name: str) -> Path:
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    return Path("data") / f"{table_name}.json"


def load_table_data(table_name: str) -> list[dict]:
    try:
        with table_path(table_name).open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError(f"Некорректные данные таблицы {table_name}.")
    return data


def save_table_data(table_name: str, data: list[dict]) -> None:
    save_json(table_path(table_name), data)


def delete_table_data(table_name: str) -> None:
    table_path(table_name).unlink(missing_ok=True)


def save_json(filepath: Path, data) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=filepath.parent, delete=False
        ) as file:
            temporary = Path(file.name)
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary, filepath)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
