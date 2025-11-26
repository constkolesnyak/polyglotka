from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from path import Path
from pydantic import AliasChoices, BaseModel, Field, model_validator

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.common.exceptions import UserError
from polyglotka.common.utils import remove_files_maybe
from polyglotka.importer.language_reactor.importer import LRSavedWord, import_lr_items
from polyglotka.importer.migaku.importer import MigakuItem, import_migaku_items


class LearningStage(StrEnum):
    LEARNING = 'LEARNING'
    KNOWN = 'KNOWN'
    SKIPPED = 'SKIPPED'


class Word(BaseModel):
    word: str
    language: str = Field(validation_alias=AliasChoices('language', 'lang_code_g'))
    learning_stage: LearningStage
    date: datetime

    def __hash__(self) -> int:
        return hash(f'{self.word},{self.language}')

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Word) and self.word == other.word

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


def import_words(cache_allowed: bool = True) -> set[Word]:
    from polyglotka.importer import words_cache

    migaku_files: list[Path] = Path(config.EXPORTED_FILES_DIR).glob(config.MGK_FILES_GLOB_PATTERN)
    lr_files: list[Path] = Path(config.EXPORTED_FILES_DIR).glob(config.LR_FILES_GLOB_PATTERN)

    if not (migaku_files + lr_files):
        files_not_found = f'Neither LR files "{config.LR_FILES_GLOB_PATTERN}" nor Migaku files "{config.MGK_FILES_GLOB_PATTERN}" are found in directory: "{config.EXPORTED_FILES_DIR}"'

        if not cache_allowed:
            raise UserError(files_not_found)
        if not config.CACHE_WORDS.exists():
            raise UserError(f'{files_not_found}\n  Cache also not found: "{config.CACHE_WORDS}"')
        pprint(f'{files_not_found}.\nUsing cache.')

        return words_cache.read()

    lr_items: list[LRSavedWord] = [i for i in import_lr_items(lr_files) if isinstance(i, LRSavedWord)]
    migaku_items: list[MigakuItem] = list(import_migaku_items(migaku_files))
    all_words: list[Word] = list(words_cache.read()) + [
        Word(**item.model_dump()) for item in (migaku_items + lr_items)
    ]

    unique_words: set[Word] = set()
    for word in sorted(all_words, key=lambda w: w.date):
        unique_words.discard(word)  # Remove older occurrences
        if word.learning_stage in (LearningStage.KNOWN, LearningStage.LEARNING):
            unique_words.add(word)

    words_cache.write(unique_words)
    remove_files_maybe(lr_files + migaku_files)

    return unique_words
