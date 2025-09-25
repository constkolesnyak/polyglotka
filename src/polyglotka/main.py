from enum import StrEnum, auto
from typing import Any

import fire  # type: ignore

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
            from polyglotka.plots.main import main

            main()


def main() -> None:
    help_page = f"""
        https://github.com/constkolesnyak/polyglotka/blob/main/README.md

        Commands: {', '.join(Command)}.
        You can override environment variables using flags.
    """
    entrypoint.__doc__ = help_page
    entrypoint.__annotations__['command'] = str

    fire.Fire(entrypoint)  # type: ignore


if __name__ == '__main__':
    main()
