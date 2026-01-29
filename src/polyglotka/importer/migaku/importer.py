from typing import Generator

import pandas as pd
from path import Path
from pydantic import BaseModel, ConfigDict, Field, computed_field

from polyglotka.common.console import Progress, ProgressType


class MigakuItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    word: str = Field(alias='dictForm')
    secondary: str = ''
    has_card: bool = Field(alias='hasCard')
    time_modified_ms: int = Field(alias='mod')
    language: str
    migaku_known_status: str = Field(alias='knownStatus')

    @computed_field
    @property
    def learning_stage(self) -> str:
        return dict(
            KNOWN='KNOWN',
            TRACKED='LEARNING',
            LEARNING='LEARNING',
            UNKNOWN='SKIPPED',
            IGNORED='SKIPPED',
        )[self.migaku_known_status]


def import_migaku_items(migaku_files: list[Path]) -> Generator[MigakuItem, None, None]:
    if not migaku_files:
        return
    with Progress(
        progress_type=ProgressType.BAR,
        text='Importing Migaku data',
        postfix='files',
        total_tasks=len(migaku_files),
    ) as progress:
        for migaku_file in migaku_files:
            dataframe: pd.DataFrame = pd.read_csv(migaku_file).fillna('')  # type: ignore
            yield from (MigakuItem.model_validate(row.to_dict()) for _, row in dataframe.iterrows())  # type: ignore
            progress.update(advance=1)


# tdc
def import_migaku_items_from_dicts(word_dicts: list[dict]) -> Generator[MigakuItem, None, None]:
    """Import MigakuItems from dictionary data (e.g., from browser automation)."""
    if not word_dicts:
        return
    with Progress(
        progress_type=ProgressType.BAR,
        text='Processing Migaku words',
        postfix='words',
        total_tasks=len(word_dicts),
    ) as progress:
        for word_dict in word_dicts:
            yield MigakuItem.model_validate(word_dict)
            progress.update(advance=1)
