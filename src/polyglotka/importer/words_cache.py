import json

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.importer.words import Word
from polyglotka.simple_commands.words_exporter import save_anki_known_morphs


def read() -> set[Word]:
    from polyglotka.importer.words import Word

    if config.CACHE_WORDS.exists():
        return {Word.model_validate(word) for word in json.loads(config.CACHE_WORDS.read_text())}
    return set()


def write(words: set[Word]) -> None:
    config.CACHE_WORDS.write_text(
        json.dumps(
            [json.loads(word.model_dump_json()) for word in words],
            indent=2,
            ensure_ascii=False,
        )
    )
    pprint(f'Cached {len(words)} words.')

    for lang in config.KNOWN_MORPHS_SAVE_LANGS.split(','):
        save_anki_known_morphs(lang, words)


def clear() -> None:
    config.CACHE_WORDS.remove_p()
    pprint(f'Cache is cleared.')
