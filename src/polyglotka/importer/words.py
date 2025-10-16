from datetime import datetime
from pathlib import Path
from typing import Any

from path import Path
from pydantic import AliasChoices, BaseModel, Field, model_validator

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.common.exceptions import UserError
from polyglotka.common.utils import remove_files_maybe
from polyglotka.importer.language_reactor.items import SavedWord, import_lr_items
from polyglotka.importer.language_reactor.structures import (
    LearningStage as LRLearningStage,
)

LearningStage = LRLearningStage


class Word(BaseModel):
    key: str
    word: str
    language: str = Field(validation_alias=AliasChoices('language', 'lang_code_g'))
    learning_stage: LearningStage
    date: datetime

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Word) and self.key == other.key

    @model_validator(mode='before')
    @classmethod
    def _(cls, data: Any) -> Any:
        if 'word' in data and isinstance(data['word'], dict):
            data['word'] = data['word']['text']
        if 'time_modified_ms' in data:
            data['date'] = datetime.fromtimestamp(
                data['time_modified_ms'] / 1000
            )  # Convert milliseconds to seconds to datetime
        return data


def import_words() -> set[Word]:
    from polyglotka.importer import words_cache

    lr_files: list[Path] = Path(config.LR_DATA_DIR).glob(config.LR_DATA_FILES_GLOB_PATTERN)
    if not lr_files:
        lr_files_not_found = f'LR files "{config.LR_DATA_FILES_GLOB_PATTERN}" are not found in directory: "{config.LR_DATA_DIR}"'
        if not words_cache.exists():
            raise UserError(f'{lr_files_not_found}\n  Cache also not found: "{words_cache.path()}"')
        pprint(f'{lr_files_not_found}. Using cache.')
        return words_cache.read()

    all_words: list[Word] = [
        Word(**item.model_dump()) for item in import_lr_items() if isinstance(item, SavedWord)
    ]

    unique_words: set[Word] = set()
    for word in sorted(all_words, key=lambda w: w.date):
        unique_words.discard(word)  # Remove older occurrences
        if word.learning_stage in (LearningStage.KNOWN, LearningStage.LEARNING):
            unique_words.add(word)

    words_cache.write(unique_words)
    pprint(f'Cached {len(unique_words)} words.')
    remove_files_maybe(lr_files)

    return unique_words
