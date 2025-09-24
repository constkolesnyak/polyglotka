from enum import StrEnum, auto
from typing import Any

import fire

from polyglotka.config import config


class Command(StrEnum):
    PLOTS = auto()


def entrypoint(command: Command, **config_upd: Any) -> None:
    if command not in list(Command):
        raise ValueError(f'Command "{command}" is invalid\n  Use one of these: ' + ', '.join(Command))

    config.override(config_upd)

    match command:
        case Command.PLOTS:
            # tdc
            from polyglotka.junk.plots import main

            main()


def run() -> None:
    help_page = f"""
        https://github.com/constkolesnyak/polyglotka/blob/main/README.md

        Args:
            command: Commands: {', '.join(Command)}.
            config_upd: You can override environment variables using flags.
    """
    entrypoint.__doc__ = help_page
    entrypoint.__annotations__['command'] = str

    fire.Fire(entrypoint)  # type: ignore


if __name__ == '__main__':
    run()
