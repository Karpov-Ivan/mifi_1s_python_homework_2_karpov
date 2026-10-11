import ast
import re

TOKEN_PATTERN = re.compile(
    r""""(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[(),=]|[^\s(),="']+"""
)


def tokenize(text: str) -> list[str]:
    tokens = []
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        match = TOKEN_PATTERN.match(text, position)
        if match is None:
            raise ValueError("Некорректные или незакрытые кавычки.")
        tokens.append(match.group())
        position = match.end()
    return tokens


def parse_value(token: str):
    if token.startswith(('"', "'")):
        try:
            value = ast.literal_eval(token)
        except (ValueError, SyntaxError) as error:
            raise ValueError(f"Некорректная строка: {token}") from error
        if isinstance(value, str):
            return value
    elif token.lower() in {"true", "false"}:
        return token.lower() == "true"
    elif re.fullmatch(r"[+-]?\d+", token):
        return int(token)
    raise ValueError(f"Некорректное значение: {token}. Строки должны быть в кавычках.")


def parse_assignments(tokens: list[str]) -> dict:
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
    tokens = tokenize(clause)
    if len(tokens) != 3:
        raise ValueError("WHERE должен содержать одно условие: столбец = значение.")
    return parse_assignments(tokens)


def parse_set(clause: str) -> dict:
    return parse_assignments(tokenize(clause))


def parse_command(text: str) -> dict:
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
