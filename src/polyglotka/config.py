from typing import Any

import pydantic_settings as pds


class _Config(pds.BaseSettings):
    PLOTS_TITLE: str = "Polyglotka Plots"
    PLOTS_BACKGROUND_COLOR: str = "#171717"

    model_config = pds.SettingsConfigDict(
        env_file=".env",
        env_prefix="POLYGLOTKA_",
        case_sensitive=True,
        extra="allow",
    )

    def override(self, config_upd: dict[str, Any]) -> None:
        config_upd = {k.upper(): v for k, v in config_upd.items()}
        if extra_vars := set(config_upd.keys()) - set(self.model_dump().keys()):
            raise ValueError(f'Invalid vars: {", ".join(extra_vars)}')
        vars(self).update(config_upd)


config = _Config()
