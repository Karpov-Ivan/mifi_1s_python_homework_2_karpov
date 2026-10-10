import prompt


def show_help() -> None:
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")


def welcome() -> None:
    print("Первая попытка запустить проект!")
    print("\n***")
    show_help()

    while True:
        command = prompt.string("Введите команду: ").strip()
        if command == "exit":
            return
        if command == "help":
            print()
            show_help()
        else:
            print(f"Неизвестная команда: {command}. Введите help для справки.")
