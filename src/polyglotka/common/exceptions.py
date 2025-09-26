from typing import Self


class UserError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(f'ERROR: {msg}')

    @classmethod
    def from_unset_env_var(cls, env_var_name: str) -> Self:
        from polyglotka.common.config import config

        return cls(
            f'{env_var_name.upper()} is unset. '
            f'Set {config.ENV_PREFIX}{env_var_name.upper()} environment variable '
            f'or pass --{env_var_name.lower()} flag'
        )
