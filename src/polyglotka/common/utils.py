from typing import Iterable

from path import Path

from polyglotka.common.config import config
from polyglotka.common.console import pprint


def remove_files_maybe(files: Iterable[str]) -> None:
    if config.RM_PROCESSED_FILES:
        for file in files:
            pprint(f'Removed "{file}".')
            Path(file).remove_p()


def run_pytest_k(test_func: str) -> None:
    import pytest
    pytest.main(['-k', test_func])
