import sys
from enum import StrEnum, auto
from typing import Any

import fire  # type: ignore
from colorama import Fore, Style

from polyglotka.common.config import config
from polyglotka.common.exceptions import UserError


class Command(StrEnum):
    PLOTS = auto()
    KANJI = auto()


def entrypoint(command: Command, **config_upd: Any) -> None:
    if command not in list(Command):
        raise UserError(f'Command "{command}" does not exist. Available commands: \n  - ' + '\n  - '.join(Command))

    config.override(config_upd)

    match command:
        case Command.PLOTS:
            from polyglotka.plots.main import main as plots_main

            plots_main()
        case Command.KANJI:
            ...  # tdc


def main() -> None:
    help_page = f"""
        https://github.com/constkolesnyak/polyglotka/blob/main/README.md

        Commands: {', '.join(Command)}.
        You can override environment variables using flags.
    """
    entrypoint.__doc__ = help_page
    entrypoint.__annotations__['command'] = str

    try:
        fire.Fire(entrypoint)  # type: ignore
    except UserError as exc:
        print(f'{Fore.RED}{exc}{Style.RESET_ALL}', file=sys.stderr)


if __name__ == '__main__':
    main()
