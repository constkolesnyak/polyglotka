import pytest

from polyglotka.common.config import _Config
from polyglotka.common.exceptions import UserError


def test_override_normalizes_lowercase_keys() -> None:
    cfg = _Config()

    cfg.override({"plots_title": "Custom title"})

    assert cfg.PLOTS_TITLE == "Custom title"


def test_override_rejects_unknown_keys() -> None:
    cfg = _Config()

    with pytest.raises(UserError) as exc:
        cfg.override({"unknown_flag": "value"})

    assert "Invalid overriding vars" in str(exc.value)


@pytest.mark.parametrize(
    "raw_value, expected",
    [
        ("1,2", (1, 2)),
        (("3", "4"), (3, 4)),
    ],
)
def test_validate_anki_min_counts_accepts_expected_inputs(raw_value, expected) -> None:
    assert _Config.validate_anki_min_counts(raw_value) == expected


@pytest.mark.parametrize("raw_value", ["1", "a,b", "1,2,3", (1,), 5])
def test_validate_anki_min_counts_rejects_invalid_inputs(raw_value) -> None:
    with pytest.raises(UserError) as exc:
        _Config.validate_anki_min_counts(raw_value)

    assert "ANKI_MIN_COUNTS" in str(exc.value)
