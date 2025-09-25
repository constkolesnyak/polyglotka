import pytest
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

console = Console()  # Singleton


def create_progress(postfix: str) -> Progress:
    return Progress(
        SpinnerColumn(style='bright_magenta'),
        BarColumn(complete_style='bright_magenta'),
        TextColumn('[bright_magenta]•'),
        TextColumn('[bright_magenta]{task.completed:,} / {task.total:,} ' + postfix),
        console=console,
        transient=True,
    )


def run_pytest_k(test_func: str) -> None:
    pytest.main(['-k', test_func])
