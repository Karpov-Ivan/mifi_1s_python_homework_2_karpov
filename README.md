# Primitive DB

Учебное консольное приложение, имитирующее работу с базой данных.

## Установка

В корневой директории репозитория выполните:

```sh
uv sync
```

Команда создаёт окружение `.venv` и устанавливает пакет и зависимости
из `uv.lock`, включая инструменты разработки.

## Запуск

Через установленную команду:

```sh
uv run project
```

## Проверка кода

```sh
uv run ruff check .
uv run ruff format --check .
```

Для форматирования:

```sh
uv run ruff format .
```

## Управление таблицами

Запуск: `uv run project`. Типы столбцов: `int`, `str`, `bool`.
Столбец `ID:int` добавляется автоматически.

- `create_table <имя> <столбец:тип> ...` — создать таблицу.
- `list_tables` — показать таблицы.
- `drop_table <имя>` — удалить таблицу.
- `help` — справка; `exit` — выход.

Пример команд внутри программы:

```text
create_table users name:str age:int is_active:bool
list_tables
drop_table users
exit
```

Метаданные сохраняются в `db_meta.json` в текущей директории.

## Демонстрация

[![Запись работы базы данных](https://asciinema.org/a/8GKq6TdJgqnBCxAg.svg)](https://asciinema.org/a/8GKq6TdJgqnBCxAg)
