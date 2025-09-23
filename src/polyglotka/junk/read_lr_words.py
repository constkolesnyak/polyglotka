from datetime import datetime
from typing import Any

import icecream
from pydantic import BaseModel, Field, field_validator, model_validator
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from polyglotka.junk.read_lr_data import LearningStage, SavedWord, read_lr_data


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
                data['time_modified_ms'] / 1000  # Convert milliseconds to seconds
            )
        return data


def read_lr_words() -> set[LRWord]:
    console = Console()
    progress = Progress(
        SpinnerColumn(style='bright_magenta'),
        BarColumn(complete_style='bright_magenta'),
        TextColumn('[bright_magenta]•'),
        TextColumn('[bright_magenta]{task.completed:,} / {task.total:,} files processed'),
        console=console,
        transient=True,
    )
    data_dir = '/Users/konst/Downloads'

    all_words: list[LRWord] = [
        LRWord(**item.model_dump())
        for item in read_lr_data(data_dir, progress)
        if isinstance(item, SavedWord)
    ]

    unique_words: set[LRWord] = set()
    for word in sorted(all_words, key=lambda w: w.date):
        unique_words.discard(word)  # Remove older
        unique_words.add(word)  # Add newer

    return unique_words
