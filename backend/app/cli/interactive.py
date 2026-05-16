from app.cli.commands import command_names


def help_text() -> str:
    return "\n".join(command_names())


def interactive_loop() -> None:
    print(help_text())
