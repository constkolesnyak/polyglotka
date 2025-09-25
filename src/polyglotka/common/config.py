from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX: str = 'POLYGLOTKA_'


class _Config(BaseSettings):  # Singleton
    LR_DATA_DIR: str = ''

    PLOTS_TITLE: str = 'Polyglotka Plots'
    PLOTS_BACKGROUND_COLOR: str = '#171717'
    PLOTS_SERVER_URL: str = 'http://127.0.0.1:8050'
    PLOTS_SMOOTH: bool = True
    PLOTS_HIDE_ALL: bool = True

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix=ENV_PREFIX,
        case_sensitive=True,
        extra='allow',
    )

    def override(self, config_upd: dict[str, Any]) -> None:
        config_upd = {k.upper(): v for k, v in config_upd.items()}
        if extra_vars := set(config_upd.keys()) - set(self.model_dump().keys()):
            raise ValueError(f'Invalid vars: {", ".join(extra_vars)}')
        vars(self).update(config_upd)


config = _Config()
