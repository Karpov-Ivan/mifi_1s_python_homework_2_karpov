import shlex

import prompt

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata

METADATA_FILE = "db_meta.json"


def print_help() -> None:
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")


def run() -> None:
    print("***База данных***")
    print_help()
    while True:
        try:
            metadata = load_metadata(METADATA_FILE)
        except (OSError, ValueError) as error:
            print(f"Ошибка чтения метаданных: {error}")
            return

        try:
            user_input = prompt.string("Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue
        if not args:
            continue

        command, *arguments = args
        previous = metadata.copy()
        if command == "create_table":
            if len(arguments) < 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            metadata = create_table(metadata, arguments[0], arguments[1:])
        elif command == "drop_table":
            if len(arguments) != 1:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            metadata = drop_table(metadata, arguments[0])
        elif command in {"list_tables", "help", "exit"}:
            if arguments:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            if command == "list_tables":
                list_tables(metadata)
            elif command == "help":
                print_help()
            else:
                return
        else:
            print(f"Функции {command} нет. Попробуйте снова.")

        if metadata != previous:
            try:
                save_metadata(METADATA_FILE, metadata)
            except OSError as error:
                print(f"Ошибка сохранения метаданных: {error}")
                return
