import prompt
from prettytable import PrettyTable

from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    get_schema,
    insert,
    list_tables,
    select,
    update,
    validate_clause,
    validate_table_data,
)
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

METADATA_FILE = "db_meta.json"


def print_help() -> None:
    print("\n***Операции с данными***")
    print("create_table <таблица> <столбец:тип> ... - создать таблицу")
    print("list_tables - показать список таблиц")
    print("drop_table <таблица> - удалить таблицу и её данные")
    print("insert into <таблица> values (<значение>, ...) - добавить запись")
    print("select from <таблица> [where <столбец> = <значение>] - прочитать записи")
    print("update <таблица> set <столбец> = <значение> where <столбец> = <значение>")
    print("delete from <таблица> where <столбец> = <значение> - удалить записи")
    print("info <таблица> - информация о таблице")
    print("Строки — в кавычках; типы: int, str, bool (true/false). ID автоматический.")
    print("Удаление требует подтверждения y; любой другой ответ отменяет операцию.")
    print("help - справка; exit - выход")


@handle_db_errors
def execute_crud(metadata: dict, request: dict) -> None:
    command = request["command"]
    table_name = request["table_name"]
    schema = get_schema(metadata, table_name)
    table_data = load_table_data(table_name)
    validate_table_data(schema, table_data)
    where_clause = request.get("where_clause")
    if where_clause is not None:
        validate_clause(schema, where_clause)

    if command == "insert":
        result = insert(metadata, table_name, request["values"])
        if result is None:
            return
        save_table_data(table_name, result)
        print(
            f"Запись с ID={result[-1]['ID']} успешно добавлена "
            f'в таблицу "{table_name}".'
        )
    elif command == "select":
        table = PrettyTable([column["name"] for column in schema])
        result = select(table_data, where_clause)
        if result is None:
            return
        for row in result:
            table.add_row([row[column["name"]] for column in schema])
        print(table)
    elif command == "info":
        columns = ", ".join(f"{c['name']}:{c['type']}" for c in schema)
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {columns}")
        print(f"Количество записей: {len(table_data)}")
    elif command in {"update", "delete"}:
        selected = select(table_data, where_clause)
        if selected is None:
            return
        if not selected:
            print("Подходящих записей нет.")
            return
        if command == "update":
            validate_clause(schema, request["set_clause"], updating=True)
            result = update(table_data, request["set_clause"], where_clause)
            action = "обновлена"
        else:
            result = delete(table_data, where_clause)
            action = "удалена"
        if result is None:
            return
        save_table_data(table_name, result)
        for row in selected:
            print(f'Запись с ID={row["ID"]} в таблице "{table_name}" успешно {action}.')


@handle_db_errors
def execute(metadata: dict, request: dict) -> None:
    command = request["command"]
    previous = metadata.copy()
    if command == "create_table":
        create_table(metadata, request["table_name"], request["columns"])
        if metadata != previous:
            save_table_data(request["table_name"], [])
            save_metadata(METADATA_FILE, metadata)
    elif command == "drop_table":
        drop_table(metadata, request["table_name"])
        if metadata != previous:
            save_metadata(METADATA_FILE, metadata)
            delete_table_data(request["table_name"])
    elif command == "list_tables":
        list_tables(metadata)
    elif command == "help":
        print_help()
    else:
        execute_crud(metadata, request)


@handle_db_errors
def read_metadata():
    return load_metadata(METADATA_FILE)


@handle_db_errors
def process_command(metadata: dict, user_input: str) -> bool:
    request = parse_command(user_input)
    if request["command"] == "exit":
        return True
    execute(metadata, request)
    return False


def run() -> None:
    print("***База данных***")
    print_help()
    while True:
        metadata = read_metadata()
        if metadata is None:
            return
        try:
            user_input = prompt.string("Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if process_command(metadata, user_input):
            return
