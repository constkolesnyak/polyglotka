from funcy import pluck_attr  # type: ignore
from path import Path

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.common.exceptions import UserError
from polyglotka.importer.words import LearningStage, Word, import_words


def get_words(learning_stage: str = config.STAGE) -> list[str]:
    imported_words: set[Word] = import_words()
    langs: set[str] = set(pluck_attr('language', imported_words))

    if config.LANG not in langs:
        raise UserError(f'LANG must be one of {tuple(langs)}, not this: {repr(config.LANG)}')

    exporting_words = (
        w.word
        for w in imported_words
        if learning_stage.upper() in (w.learning_stage, '') and w.language == config.LANG
    )
    return sorted(exporting_words)


def print_words() -> None:
    print('\n'.join(get_words()))


def save_anki_known_morphs() -> None:
    known_morphs_file = (
        Path(config.ANKI_KNOWN_MORPHS_DIR) / f'{config.APP_NAME}_known_morphs_{config.LANG}.csv'
    )
    known_morphs_file.write_text('Morph-Lemma\n' + '\n'.join(get_words(LearningStage.KNOWN)))
    pprint(f'Saved known morphs: "{known_morphs_file}"')
