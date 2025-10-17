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

    @computed_field
    @property
    def key(self) -> str:
        return self.word


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
