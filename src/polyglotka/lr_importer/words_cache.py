import json
from typing import Iterable

from path import Path
from platformdirs import user_cache_dir

from polyglotka.common.config import config
from polyglotka.lr_importer.lr_words import LRWord


def path() -> Path:
    cache_dir = Path(user_cache_dir(config.APP_NAME))
    cache_dir.mkdir_p()
    return cache_dir / 'words.json'


def exists() -> bool:
    return path().exists()


def read() -> set[LRWord]:
    from polyglotka.lr_importer.lr_words import LRWord

    return {LRWord.model_validate(word) for word in json.loads(path().read_text())}


def write(lr_words: Iterable[LRWord]) -> None:
    path().write_text(
        json.dumps(
            [json.loads(word.model_dump_json()) for word in lr_words],
            indent=2,
            ensure_ascii=False,
        )
    )
