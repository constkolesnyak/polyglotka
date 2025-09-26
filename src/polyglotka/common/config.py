from typing import Any

import icecream
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from polyglotka.common.exceptions import UserError


class _Config(BaseSettings):  # Singleton
    ENV_PREFIX: str = 'POLYGLOTKA_'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix=ENV_PREFIX,
        case_sensitive=True,
        extra='allow',
    )

    LR_DATA_DIR: str = ''

    PLOTS_TITLE: str = 'Polyglotka Plots'
    PLOTS_BACKGROUND_COLOR: str = '#171717'
    PLOTS_SERVER_URL: str = 'http://127.0.0.1:8050'
    PLOTS_SMOOTH: bool = True
    PLOTS_HIDE_ALL: bool = True

    ANKI_MIN_COUNTS: tuple[int, int] | None = None
    ANKI_FILTERS: str = 'deck:漢字 is:suspended'
    ANKI_FIELD: str = 'kanji'

    @staticmethod
    def get_anki_min_counts(min_counts_arg: str | tuple[Any, ...] | None) -> tuple[int, int] | None:
        if min_counts_arg is None:
            return min_counts_arg
        try:
            if isinstance(min_counts_arg, tuple):
                min_counts_arg = ','.join(map(str, min_counts_arg))
            min_counts = tuple(map(int, min_counts_arg.split(',')))
            assert len(min_counts) == 2
            return min_counts
        except (ValueError, AssertionError, AttributeError):

            raise UserError(
                f'ANKI_MIN_COUNTS must be 2 integers separated by a comma, not this: {min_counts_arg}'
            )

    @field_validator('ANKI_MIN_COUNTS', mode='before')
    @classmethod
    def _(cls, value: Any) -> tuple[int, int] | None:
        return cls.get_anki_min_counts(value)

    def override(self, config_upd: dict[str, Any]) -> None:
        config_upd = {k.upper(): v for k, v in config_upd.items()}
        if extra_vars := set(config_upd.keys()) - set(self.model_dump().keys()):
            raise UserError(f'Invalid overriding vars: {", ".join(extra_vars)}')

        vars(self).update(config_upd)
        self.get_anki_min_counts(self.ANKI_MIN_COUNTS)

        # icecream.ic(config.model_dump())
        # exit(0)


config = _Config()
