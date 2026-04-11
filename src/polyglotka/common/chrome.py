"""Shared helpers for reading data out of Chrome's local storage."""

import platform

from path import Path

from polyglotka.common.config import config
from polyglotka.common.exceptions import UserError


def get_chrome_profile_path() -> Path:
    """Auto-detect Chrome user data directory (override with CHROME_DATA_DIR)."""
    if config.CHROME_DATA_DIR:
        profile_path = Path(config.CHROME_DATA_DIR)
        if not profile_path.exists():
            raise UserError(f'Chrome profile path not found: {profile_path}')
        return profile_path

    system = platform.system()
    home = Path.home()

    if system == 'Darwin':
        base_path = home / 'Library/Application Support/Google/Chrome'
    elif system == 'Windows':
        base_path = home / 'AppData/Local/Google/Chrome/User Data'
    elif system == 'Linux':
        base_path = home / '.config/google-chrome'
    else:
        raise UserError(f'Unsupported platform: {system}. Please set CHROME_DATA_DIR manually.')

    if not base_path.exists():
        raise UserError(
            f'Chrome data not found at: {base_path}\n'
            'Please install Chrome or set CHROME_DATA_DIR variable.'
        )
    return base_path


CHROME_PROFILE_NAMES = ['Default', 'Profile 1', 'Profile 2', 'Profile 3', 'Profile 4', 'Profile 5']
