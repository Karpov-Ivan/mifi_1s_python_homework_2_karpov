import json

from primitive_db.constants import STRING_QUOTES, TOKEN_SEPARATORS


def tokenize(text: str) -> list[str]:
    """Разделяет команду на токены, сохраняя кавычки и экранирование."""
    tokens = []
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        start = position
        character = text[position]
        if character in TOKEN_SEPARATORS:
            position += 1
        elif character in STRING_QUOTES:
            quote = character
            position += 1
            while position < len(text) and text[position] != quote:
                if text[position] == "\\":
                    position += 1
                position += 1
            if position >= len(text):
                raise ValueError("Некорректные или незакрытые кавычки.")
            position += 1
        else:
            while (
                position < len(text)
                and not text[position].isspace()
                and text[position] not in TOKEN_SEPARATORS + STRING_QUOTES
            ):
                position += 1
        tokens.append(text[start:position])
    return tokens


def parse_string(token: str) -> str:
    """Преобразует строковый литерал в кавычках в значение Python."""
    if len(token) < 2 or token[-1] != token[0]:
        raise ValueError(f"Некорректная строка: {token}")
    if token[0] == '"':
        return json.loads(token)
    body = token[1:-1]
    encoded = []
    position = 0
    while position < len(body):
        character = body[position]
        if character == "\\":
            position += 1
            if position == len(body):
                raise ValueError(f"Некорректная строка: {token}")
            if body[position] == "'":
                encoded.append("'")
            else:
                encoded.extend(("\\", body[position]))
        elif character == '"':
            encoded.append('\\"')
        else:
            encoded.append(character)
        position += 1
    return json.loads('"' + "".join(encoded) + '"')


def parse_value(token: str):
    """Разбирает строковое, целочисленное или логическое значение."""
    if token.startswith(tuple(STRING_QUOTES)):
        return parse_string(token)
    if token.lower() in {"true", "false"}:
        return token.lower() == "true"
    digits = token[1:] if token.startswith(("+", "-")) else token
    if digits and digits.isdecimal():
        return int(token)
    raise ValueError(f"Некорректное значение: {token}. Строки должны быть в кавычках.")


def parse_assignments(tokens: list[str]) -> dict:
    """Преобразует присваивания в словарь без повторяющихся столбцов."""
    result = {}
    while tokens:
        if len(tokens) < 3 or tokens[1] != "=" or not tokens[0].isidentifier():
            raise ValueError("Ожидается условие вида столбец = значение.")
        name = tokens[0]
        if name in result:
            raise ValueError(f"Столбец {name} указан повторно.")
        result[name] = parse_value(tokens[2])
        tokens = tokens[3:]
        if tokens:
            if tokens[0] != "," or len(tokens) == 1:
                raise ValueError("Присваивания должны быть разделены запятыми.")
            tokens = tokens[1:]
    if not result:
        raise ValueError("Необходимо указать столбец и значение.")
    return result


def parse_where(clause: str) -> dict:
    """Разбирает одно условие равенства для фильтрации записей."""
    tokens = tokenize(clause)
    if len(tokens) != 3:
        raise ValueError("WHERE должен содержать одно условие: столбец = значение.")
    return parse_assignments(tokens)


def parse_set(clause: str) -> dict:
    """Разбирает список присваиваний для обновления записи."""
    return parse_assignments(tokenize(clause))


def parse_command(text: str) -> dict:
    """Проверяет синтаксис команды и возвращает её разобранные аргументы."""
    tokens = tokenize(text)
    if not tokens:
        raise ValueError("Введите команду.")
    command = tokens[0].lower()
    result = {"command": command}
    if command in {"help", "exit", "list_tables"}:
        if len(tokens) != 1:
            raise ValueError(f"Команда {command} не принимает аргументов.")
        return result
    if command in {"create_table", "drop_table", "info"}:
        if len(tokens) < 2 or (command != "create_table" and len(tokens) != 2):
            raise ValueError(f"Некорректные аргументы команды {command}.")
        result["table_name"] = tokens[1]
        if command == "create_table":
            if len(tokens) < 3:
                raise ValueError("Укажите хотя бы один столбец: имя:тип.")
            result["columns"] = tokens[2:]
    elif command == "insert":
        if (
            len(tokens) < 7
            or tokens[1].lower() != "into"
            or tokens[3].lower() != "values"
            or tokens[4] != "("
            or tokens[-1] != ")"
        ):
            raise ValueError("Формат: insert into таблица values (значение, ...).")
        result["table_name"] = tokens[2]
        value_tokens = tokens[5:-1]
        if len(value_tokens) % 2 != 1 or any(
            value_tokens[i] != "," for i in range(1, len(value_tokens), 2)
        ):
            raise ValueError("Значения должны быть разделены запятыми.")
        result["values"] = [parse_value(t) for t in value_tokens[::2]]
    elif command in {"select", "delete"}:
        if len(tokens) < 3 or tokens[1].lower() != "from":
            raise ValueError(
                f"Формат: {command} from таблица [where столбец = значение]."
            )
        result["table_name"] = tokens[2]
        if len(tokens) == 3 and command == "select":
            result["where_clause"] = None
        elif len(tokens) == 7 and tokens[3].lower() == "where":
            result["where_clause"] = parse_where(" ".join(tokens[4:]))
        else:
            raise ValueError("Укажите WHERE в формате: where столбец = значение.")
    elif command == "update":
        if len(tokens) < 10 or tokens[2].lower() != "set":
            raise ValueError("Формат: update таблица set столбец = значение where ...")
        where_positions = [
            i for i in range(6, len(tokens), 4) if tokens[i].lower() == "where"
        ]
        if len(where_positions) != 1:
            raise ValueError("Укажите одно условие WHERE.")
        position = where_positions[0]
        result["table_name"] = tokens[1]
        result["set_clause"] = parse_set(" ".join(tokens[3:position]))
        result["where_clause"] = parse_where(" ".join(tokens[position + 1 :]))
    else:
        raise ValueError(f"Функции {tokens[0]} нет. Попробуйте снова.")
    if not result["table_name"].isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {result['table_name']}.")
    return result
