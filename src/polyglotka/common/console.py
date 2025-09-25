import sys
from enum import StrEnum, auto
from types import TracebackType
from typing import Optional, Self, Type

from rich.console import Console
from rich.progress import BarColumn
from rich.progress import Progress as RichProgress
from rich.progress import SpinnerColumn, TextColumn

_console = Console(file=sys.stderr, force_terminal=True)  # Singleton


class ProgressType(StrEnum):
    BAR = auto()
    TEXT = auto()


class Progress:
    def __init__(
        self,
        progress_type: ProgressType,
        text: str,
        postfix: str = '',
        total_tasks: int | None = None,
        color: str = 'bright_magenta',
    ) -> None:
        self.progress_type = progress_type
        self.text = text + '...'
        self.postfix = postfix
        self.total_tasks = total_tasks
        self.color = color

    def __enter__(self) -> Self:
        match self.progress_type:
            case ProgressType.BAR:
                self.rich_progress = RichProgress(
                    SpinnerColumn(style=self.color),
                    TextColumn(f'[{self.color}]{{task.description}} |'),
                    BarColumn(complete_style=self.color),
                    TextColumn(f'[{self.color}]| {{task.completed:,}} / {{task.total:,}} ' + self.postfix),
                    console=_console,
                    transient=True,
                )
            case ProgressType.TEXT:
                self.rich_progress = RichProgress(
                    SpinnerColumn(style=self.color),
                    TextColumn(f'[{self.color}]{{task.description}}'),
                    console=_console,
                    transient=True,
                )
            case _:
                self.rich_progress = RichProgress()

        self.rich_progress.__enter__()
        self.task = self.rich_progress.add_task(self.text, total=self.total_tasks)
        return self

    def update(self, text: str = '', advance: int = 0) -> None:
        self.rich_progress.update(self.task, advance=advance)
        if text:
            self.rich_progress.update(self.task, description=f'[{self.color}]{text}...')

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.rich_progress.__exit__(exc_type, exc_val, exc_tb)
