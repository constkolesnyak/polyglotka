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


def read_lr_words():
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

    lr_words: set[LRWord] = set()
    for item in read_lr_data(data_dir, progress):
        if isinstance(item, SavedWord):
            lr_word = LRWord(**item.model_dump())
            icecream.ic(lr_word)


# tdc VVV move to tests


def main(max_display: int = 5) -> None:
    """Main function to process and display language learning data.

    Args:
        max_display: Maximum number of items to display in detail
    """
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

    print(f"Reading data with full SavedItem models...")
    print(f"Will display first {max_display} items in detail.")

    total_items = 0
    word_count = 0
    phrase_count = 0

    try:
        for item in read_lr_data(data_dir, progress):
            total_items += 1

            if total_items <= max_display:
                try:
                    lr_word = LRWord(**item.model_dump())
                    icecream.ic(lr_word)
                except Exception as e:
                    print(f"Failed to convert item {total_items} to LRWord: {e}")
                    print(f"Item type: {type(item).__name__}")
                    print(f"Item keys: {list(item.model_dump().keys())}")

    except Exception as e:
        print(f"\nError during processing: {e}")
        return

    print(f'\n=== Final Summary ===')
    print(f'Total items processed: {total_items:,}')
    print(f'Words: {word_count:,}')
    print(f'Phrases: {phrase_count:,}')
    print(f'Other/Unknown: {total_items - word_count - phrase_count:,}')


if __name__ == "__main__":
    read_lr_words()
