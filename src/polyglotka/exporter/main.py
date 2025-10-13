from funcy import pluck_attr  # type: ignore

from polyglotka.common.config import config
from polyglotka.common.exceptions import UserError
from polyglotka.importer.words import Word, import_words


def main() -> None:
    imported_words: set[Word] = import_words()
    langs: set[str] = set(pluck_attr('language', imported_words))

    if config.LANG not in langs:
        raise UserError(f'LANG must be one of {tuple(langs)}, not this: {repr(config.LANG)}')

    exporting_words = (
        w.word
        for w in imported_words
        if w.learning_stage == (config.STAGE.upper() or 'KNOWN') and w.language == config.LANG
    )
    print('\n'.join(sorted(exporting_words)))
