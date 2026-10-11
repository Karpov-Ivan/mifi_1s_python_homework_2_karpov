# Primitive DB

Учебное консольное приложение, имитирующее работу с базой данных.

## Установка

В корневой директории репозитория выполните:

```sh
make install
```

Эквивалент без Make: `uv sync`. Требуются Python 3.12+ и `uv`.

Команда создаёт окружение `.venv` и устанавливает пакет и зависимости
из `uv.lock`, включая инструменты разработки.

## Запуск

Через установленную команду:

```sh
make run
```

Эквивалент без Make: `uv run database`.

## Проверка кода

```sh
make lint
```

Проверяет Ruff и форматирование.

Для форматирования:

```sh
uv run ruff format .
```

## Управление таблицами

Запуск: `uv run database`. Типы столбцов: `int`, `str`, `bool`.
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

## CRUD-операции

Строки указываются в кавычках, логические значения — `true`/`false`.
Все поля обязательны; `ID` генерируется автоматически.

- `insert into ... values (...)` — добавить запись без передачи ID.
- `select from ... [where ...]` — вывести все записи или выборку.
- `update ... set ... where ...` — изменить подходящие записи.
- `delete from ... where ...` — удалить подходящие записи.
- `info <таблица>` — показать столбцы и количество записей.

```text
create_table users name:str age:int is_active:bool
insert into users values ("Sergei", 28, true)
select from users
select from users where age = 28
update users set age = 29 where name = "Sergei"
delete from users where ID = 1
info users
```

Данные таблиц хранятся в `data/<имя_таблицы>.json` в текущей директории.

### Демонстрация CRUD

[![Запись CRUD-операций](https://asciinema.org/a/sCEivTaO7Wnzo0ow.svg)](https://asciinema.org/a/sCEivTaO7Wnzo0ow)

## Декораторы и кэширование

- Ошибки команд обрабатываются централизованно без завершения программы.
- Удаление таблиц и записей требует подтверждения `y`; другой ответ отменяет действие.
- Для `insert` и `select` выводится время выполнения.
- Повторные `select` используют кэш замыкания; изменения данных учитываются автоматически.

### Финальная демонстрация

[![Декораторы и подтверждение удаления](https://asciinema.org/a/4xHMVjgzSbJxPAJC.svg)](https://asciinema.org/a/4xHMVjgzSbJxPAJC)

### Полный сценарий

[![Полный цикл работы базы данных](https://asciinema.org/a/CTY8O5ap9nflHS68.svg)](https://asciinema.org/a/CTY8O5ap9nflHS68)
