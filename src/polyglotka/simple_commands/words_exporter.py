import icecream
from funcy import pluck_attr  # type: ignore
from path import Path

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.common.exceptions import UserError
from polyglotka.importer.words import LearningStage, Word, import_words


def create_word_list(lang: str = '', stage: str = '', words: set[Word] | None = None) -> list[str]:
    lang = lang or config.LANG
    stage = stage or config.STAGE
    imported_words: set[Word] = words or import_words()

    langs: set[str] = set(pluck_attr('language', imported_words))
    if lang not in langs:
        raise UserError(f'LANG must be one of {tuple(langs)}, not this: {repr(lang)}')

    word_list = (
        w.word for w in imported_words if stage.upper() in (w.learning_stage, '') and w.language == lang
    )
    return sorted(word_list)


def print_words() -> None:
    print('\n'.join(create_word_list()))


def save_anki_known_morphs(lang: str = '', words: set[Word] | None = None) -> None:
    lang = lang or config.LANG
    word_list = create_word_list(lang, LearningStage.KNOWN, words)
    known_morphs_file = Path(config.ANKI_KNOWN_MORPHS_DIR) / f'{config.APP_NAME}_known_morphs_{lang}.csv'

    known_morphs_file.write_text('Morph-Lemma\n' + '\n'.join(word_list))
    pprint(f'Saved {len(word_list)} known morphs ({lang}): "{known_morphs_file}".')
