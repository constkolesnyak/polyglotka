from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from polyglotka.lr_importer.lr_items import LearningStage, SavedWord, import_lr_items


class LRWord(BaseModel):
    key: str
    word: str
    language: str = Field(alias='lang_code_g')
    learning_stage: LearningStage
    date: datetime

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LRWord) and self.key == other.key

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


def import_lr_words() -> set[LRWord]:
    all_words: list[LRWord] = [LRWord(**item.model_dump()) for item in import_lr_items() if isinstance(item, SavedWord)]

    unique_words: set[LRWord] = set()
    for word in sorted(all_words, key=lambda w: w.date):
        unique_words.discard(word)  # Remove older
        unique_words.add(word)  # Add newer

    return unique_words
