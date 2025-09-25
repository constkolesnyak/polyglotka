import pytest


def run_pytest_k(test_func: str) -> None:
    pytest.main(['-k', test_func])
