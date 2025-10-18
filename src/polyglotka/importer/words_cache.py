import json

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.importer.words import Word


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


def clear() -> None:
    config.CACHE_WORDS.remove_p()
    pprint(f'Cache is cleared.')
