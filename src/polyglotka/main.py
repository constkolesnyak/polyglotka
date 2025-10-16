import sys
from enum import StrEnum, auto
from typing import Any

import fire  # type: ignore
import icecream

from polyglotka.common.config import config
from polyglotka.common.exceptions import UserError
from polyglotka.importer import words_cache
from polyglotka.plots.main import main as plots_main
from polyglotka.simple_commands.excel_to_srt import main as excel_to_srt_main
from polyglotka.simple_commands.kanji import main as kanji_main
from polyglotka.simple_commands.words_exporter import main as words_exporter_main


class Command(StrEnum):
    INFO = auto()
    PLOTS = auto()
    KANJI = auto()
    ANKI = auto()
    WORDS = auto()
    SUBS = auto()


def entrypoint(command: Command, **config_upd: Any) -> None:
    if command not in list(Command):
        raise UserError(
            f'Command "{command}" does not exist. Available commands: \n  - ' + '\n  - '.join(Command)
        )
    config.override(config_upd)

    match command:
        case Command.INFO:
            icecream.ic(config.model_dump())
            icecream.ic(words_cache.path())
        case Command.PLOTS:
            plots_main()
        case Command.KANJI:
            kanji_main()
        case Command.ANKI:
            kanji_main(anki=True)
        case Command.WORDS:
            words_exporter_main()
        case Command.SUBS:
            excel_to_srt_main()


def main() -> None:
    help_page = f'''
        https://github.com/constkolesnyak/polyglotka/blob/main/README.md

        Commands: {', '.join(Command)}.
        You can override environment variables using flags.
    '''
    entrypoint.__doc__ = help_page
    entrypoint.__annotations__['command'] = str

    try:
        fire.Fire(entrypoint)  # type: ignore
    except UserError as exc:
        print(exc, file=sys.stderr)


if __name__ == '__main__':
    main()
