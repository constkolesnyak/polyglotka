from functools import cached_property
from typing import Any

from path import Path
from platformdirs import user_cache_dir
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from polyglotka.common.exceptions import UserError


class _Config(BaseSettings):  # Singleton
    APP_NAME: str = 'polyglotka'
    ENV_PREFIX: str = f'{APP_NAME.upper()}_'
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, case_sensitive=True)

    RM_PROCESSED_FILES: bool = True
    NATIVE_LANG: str = 'en'

    # CLI args
    NAME: str = ''
    START: int = 1
    STAGE: str = ''
    LANG: str = ''

    CACHE_DIR: Path = Path(user_cache_dir(APP_NAME)).mkdir_p()
    CACHE_WORDS: Path = CACHE_DIR / 'words.json'

    EXPORTED_FILES_DIR: str = Path.home() / 'Downloads'
    LR_FILES_GLOB_PATTERN: str = 'lln_json_items_*.json'
    MGK_FILES_GLOB_PATTERN: str = 'migaku_words_*.csv'

    LR_SUBS_GLOB_PATTERN: str = 'lln_excel_subs_*.xlsx'
    LR_SUBS_MS_PER_CHAR: int = 80
    SRT_SUBS_TARGET_DIR: str = EXPORTED_FILES_DIR
    SRT_SUBS_TRASH_DIR: str = EXPORTED_FILES_DIR

    PLOTS_TITLE: str = 'Polyglotka Plots'
    PLOTS_BACKGROUND_COLOR: str = '#171717'
    PLOTS_SERVER_URL: str = 'http://127.0.0.1:8050'
    PLOTS_SMOOTH: bool = True
    PLOTS_AGGREGATE: bool = True
    PLOTS_LEARNING_STAGES: str = 'LEARNING,KNOWN,SKIPPED'
    PLOTS_Y_MIN: int = 0
    PLOTS_X_DAYS_DELTA: int | None = None
    PLOTS_Y_TITLE: str = 'Word Count'

    ANKI_MIN_COUNTS: tuple[int, int] | str = (0, 0)
    ANKI_FILTERS: str = 'deck:漢字 is:suspended'
    ANKI_KANJI_FIELD: str = 'kanji'

    KNOWN_MORPHS_DIR: str = EXPORTED_FILES_DIR
    KNOWN_MORPHS_SAVE_LANGS: str = ''  # Example: 'ja,de'

    @cached_property
    def plots_learning_stages(self):
        from polyglotka.importer.words import LearningStage

        return {LearningStage(stage) for stage in self.PLOTS_LEARNING_STAGES.upper().split(',')}

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
        for directory in (self.EXPORTED_FILES_DIR, self.SRT_SUBS_TARGET_DIR, self.KNOWN_MORPHS_DIR):
            if not Path(directory).is_dir():
                raise UserError(f'Directory not found: {directory}')


config = _Config()
