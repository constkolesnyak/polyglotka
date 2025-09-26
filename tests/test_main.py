from __future__ import annotations

from typing import Any

import pytest

from polyglotka.common.exceptions import UserError
from polyglotka.main import Command, entrypoint


class DummyConfig:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def override(self, config_upd: dict[str, Any]) -> None:
        self.calls.append(config_upd)


def test_entrypoint_routes_to_plots(monkeypatch) -> None:
    dummy_config = DummyConfig()
    called: dict[str, bool] = {"plots": False}

    def fake_plots() -> None:
        called["plots"] = True

    monkeypatch.setattr("polyglotka.main.plots_main", fake_plots)
    monkeypatch.setattr("polyglotka.main.config", dummy_config)

    entrypoint(Command.PLOTS, lr_data_dir="/tmp/language-reactor")

    assert called["plots"] is True


def test_entrypoint_rejects_unknown_command(monkeypatch) -> None:
    dummy_config = DummyConfig()
    monkeypatch.setattr("polyglotka.main.config", dummy_config)

    with pytest.raises(UserError) as exc:
        entrypoint("UNKNOWN")  # type: ignore[arg-type]

    assert 'Command "UNKNOWN" does not exist' in str(exc.value)
    assert dummy_config.calls == []
