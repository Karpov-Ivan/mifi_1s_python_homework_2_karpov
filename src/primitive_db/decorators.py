import time

from primitive_db.constants import CONFIRM_RESPONSE


def preserve_function(func):
    """Создаёт декоратор для сохранения имени и описания функции."""

    def decorator(wrapper):
        """Переносит сведения исходной функции на обёртку."""
        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__annotations__ = func.__annotations__.copy()
        wrapper.__wrapped__ = func
        return wrapper

    return decorator


def copy_value(value):
    """Копирует вложенные словари, списки и кортежи для защиты кэша."""
    if isinstance(value, dict):
        return {key: copy_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copy_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(copy_value(item) for item in value)
    return value


def handle_db_errors(func):
    """Обрабатывает ошибки операции и возвращает None при неудаче."""

    @preserve_function(func)
    def wrapper(*args, **kwargs):
        """Вызывает операцию и выводит сообщение при ошибке."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлами: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return wrapper


def confirm_action(action_name):
    """Создаёт декоратор, запрашивающий подтверждение опасного действия."""

    def decorator(func):
        """Оборачивает функцию запросом подтверждения действия."""

        @preserve_function(func)
        def wrapper(*args, **kwargs):
            """Выполняет действие только после ответа y."""
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                print()
                answer = "n"
            if answer.strip().lower() != CONFIRM_RESPONSE:
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Добавляет вывод времени выполнения обёрнутой функции."""

    @preserve_function(func)
    def wrapper(*args, **kwargs):
        """Вызывает функцию и выводит затраченное время."""
        started = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")

    return wrapper


def create_cacher():
    """Создаёт замыкание для кэширования результатов по ключу."""
    cache = {}

    def cache_result(key, value_func):
        """Вычисляет результат один раз для ключа и возвращает его копию."""
        if key not in cache:
            cache[key] = copy_value(value_func())
        return copy_value(cache[key])

    return cache_result
