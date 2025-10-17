import json

from path import Path
from platformdirs import user_cache_dir

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.importer.words import Word


def path() -> Path:
    cache_dir = Path(user_cache_dir(config.APP_NAME))
    cache_dir.mkdir_p()
    return cache_dir / 'words.json'


def exists() -> bool:
    return path().exists()


def read() -> set[Word]:
    from polyglotka.importer.words import Word

    if exists():
        return {Word.model_validate(word) for word in json.loads(path().read_text())}
    return set()


def write(words: set[Word]) -> None:
    path().write_text(
        json.dumps(
            [json.loads(word.model_dump_json()) for word in words],
            indent=2,
            ensure_ascii=False,
        )
    )
    pprint(f'Cached {len(words)} words.')


def clear() -> None:
    path().remove_p()
    pprint(f'Cache is cleared.')
