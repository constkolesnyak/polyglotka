import pytest
from path import Path

from polyglotka.common.config import config
from polyglotka.common.console import pprint


def remove_files_maybe(files: list[str] | list[Path]) -> None:
    if config.PROCESSED_FILES_RM:
        for file in files:
            pprint(f'Removed "{file}".')
            Path(file).remove_p()


def run_pytest_k(test_func: str) -> None:
    pytest.main(['-k', test_func])
