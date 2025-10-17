import sys
from enum import StrEnum, auto
from types import TracebackType
from typing import Any, Optional, Self, Type

from pydantic import BaseModel, ConfigDict
from rich.console import Console
from rich.progress import BarColumn
from rich.progress import Progress as RichProgress
from rich.progress import SpinnerColumn, TextColumn

_console = Console(file=sys.stderr, force_terminal=True)  # Singleton
COLOR = 'bright_magenta'


class ProgressType(StrEnum):
    BAR = auto()
    TEXT = auto()


def pprint(*args: Any) -> None:
    _console.print(*args, style=COLOR)


class Progress(BaseModel):
    model_config = ConfigDict(extra='allow')

    progress_type: ProgressType
    text: str
    postfix: str = ''
    total_tasks: int | None = None
    color: str = COLOR

    def __enter__(self) -> Self:
        self.text = f'{self.text:<21}'

        match self.progress_type:
            case ProgressType.BAR:
                self.rich_progress = RichProgress(
                    SpinnerColumn(style=self.color),
                    TextColumn(f'[{self.color}]{{task.description}} |'),
                    BarColumn(complete_style=self.color),
                    TextColumn(f'[{self.color}]| {{task.completed:,}} / {{task.total:,}} ' + self.postfix),
                    console=_console,
                    # transient=True,
                )
            case ProgressType.TEXT:
                self.rich_progress = RichProgress(
                    SpinnerColumn(style=self.color),
                    TextColumn(f'[{self.color}]{{task.description}}'),
                    console=_console,
                    # transient=True,
                )
            case _:
                self.rich_progress = RichProgress()

        self.rich_progress.__enter__()
        self.task = self.rich_progress.add_task(self.text, total=self.total_tasks)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.rich_progress.__exit__(exc_type, exc_val, exc_tb)

    def update(self, text: str = '', advance: int = 0) -> None:
        self.rich_progress.update(self.task, advance=advance)
        if text:
            self.rich_progress.update(self.task, description=f'[{self.color}]{text}...')
