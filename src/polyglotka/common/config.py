from typing import Any

from path import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from polyglotka.common.exceptions import UserError


class _Config(BaseSettings):  # Singleton
    APP_NAME: str = 'polyglotka'
    ENV_PREFIX: str = f'{APP_NAME.upper()}_'
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, case_sensitive=True)

    EXPORTED_FILES_DIR: str = Path.home() / 'Downloads'
    LR_FILES_GLOB_PATTERN: str = 'lln_json_items_*.json'
    MGK_FILES_GLOB_PATTERN: str = 'migaku_words_*.csv'

    LR_SUBS_GLOB_PATTERN: str = 'lln_excel_subs_*.xlsx'
    LR_SUBS_MS_PER_CHAR: int = 80
    SRT_SUBS_TARGET_DIR: str = EXPORTED_FILES_DIR

    PROCESSED_FILES_RM: bool = True

    PLOTS_TITLE: str = 'Polyglotka Plots'
    PLOTS_BACKGROUND_COLOR: str = '#171717'
    PLOTS_SERVER_URL: str = 'http://127.0.0.1:8050'
    PLOTS_SMOOTH: bool = True
    PLOTS_HIDE_AGGR: bool = True

    ANKI_MIN_COUNTS: tuple[int, int] | str = (0, 0)
    ANKI_FILTERS: str = 'deck:漢字 is:suspended'
    ANKI_KANJI_FIELD: str = 'kanji'

    STAGE: str = ''
    LANG: str = ''

    @property
    def anki_min_counts(self) -> tuple[int, int]:
        assert isinstance(self.ANKI_MIN_COUNTS, tuple)
        return self.ANKI_MIN_COUNTS

    @staticmethod
    def validate_anki_min_counts(min_counts_arg: str | tuple[Any, ...]) -> tuple[int, int]:
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
    def _(cls, value: Any) -> tuple[int, int]:
        return cls.validate_anki_min_counts(value)

    def override(self, config_upd: dict[str, Any]) -> None:
        config_upd = {k.upper(): v for k, v in config_upd.items()}
        if extra_vars := set(config_upd.keys()) - set(self.model_dump().keys()):
            raise UserError(f'Invalid overriding vars: {", ".join(extra_vars)}')

        vars(self).update(config_upd)

        self.validate_anki_min_counts(self.ANKI_MIN_COUNTS)
        for directory in (self.EXPORTED_FILES_DIR, self.SRT_SUBS_TARGET_DIR):
            if not Path(directory).exists():
                raise UserError(f'Directory not found: {directory}')


config = _Config()
