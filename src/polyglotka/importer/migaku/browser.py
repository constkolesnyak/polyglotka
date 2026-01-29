"""Direct Migaku IndexedDB import by reading Chrome's storage files from disk."""

import platform
import sqlite3
import tempfile
import zlib
from typing import Any, Generator

from path import Path

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.common.exceptions import UserError
from polyglotka.importer.migaku.importer import MigakuItem

MIGAKU_DOMAIN = 'https_study.migaku.com_0'


def _get_chrome_profile_path() -> Path:
    """Auto-detect Chrome user data directory based on platform."""
    if config.CHROME_DATA_DIR:
        profile_path = Path(config.CHROME_DATA_DIR)
        if not profile_path.exists():
            raise UserError(f'Chrome profile path not found: {profile_path}')
        return profile_path

    system = platform.system()
    home = Path.home()

    if system == 'Darwin':  # macOS
        base_path = home / 'Library/Application Support/Google/Chrome'
    elif system == 'Windows':
        base_path = home / 'AppData/Local/Google/Chrome/User Data'
    elif system == 'Linux':
        base_path = home / '.config/google-chrome'
    else:
        raise UserError(f'Unsupported platform: {system}. Please set MIGAKU_CHROME_PROFILE manually.')

    if not base_path.exists():
        raise UserError(
            f'Chrome data not found at: {base_path}\n'
            'Please install Chrome or set CHROME_DATA_DIR variable.'
        )
    return base_path


def _find_migaku_blob_path(chrome_path: Path) -> Path:
    """Find the Migaku IndexedDB blob storage path."""
    # Check common profile locations
    profile_names = ['Default', 'Profile 1', 'Profile 2', 'Profile 3', 'Profile 4', 'Profile 5']

    for profile_name in profile_names:
        blob_dir = chrome_path / profile_name / 'IndexedDB' / f'{MIGAKU_DOMAIN}.indexeddb.blob'
        if blob_dir.exists():
            return blob_dir

    # Try to find it by searching
    for profile_dir in chrome_path.dirs():
        blob_dir = profile_dir / 'IndexedDB' / f'{MIGAKU_DOMAIN}.indexeddb.blob'
        if blob_dir.exists():
            return blob_dir

    raise UserError(
        'Migaku data not found in any Chrome profile.\n'
        'Please make sure you are logged into Migaku at https://study.migaku.com in Chrome.'
    )


def _find_sqlite_blob(blob_dir: Path) -> Path:
    """Find the SQLite blob file (largest file in blob storage)."""
    blob_files = list(blob_dir.walkfiles())
    if not blob_files:
        raise UserError(
            'Migaku blob storage is empty.\n'
            'Please make sure you are logged into Migaku at https://study.migaku.com in Chrome.'
        )

    # The SQLite database blob is the largest file
    largest_blob = max(blob_files, key=lambda f: f.getsize())
    return largest_blob


def _decompress_blob(blob_path: Path) -> bytes:
    """Decompress the gzipped SQLite blob from Chrome's IndexedDB storage."""
    with open(blob_path, 'rb') as f:
        data = f.read()

    # Find gzip magic bytes (1f 8b)
    gzip_start = data.find(b'\x1f\x8b')
    if gzip_start < 0:
        raise UserError('Invalid Migaku blob format: gzip header not found.')

    # Skip the 10-byte gzip header and decompress using raw deflate
    compressed = data[gzip_start + 10 :]

    try:
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
        return decompressor.decompress(compressed)
    except zlib.error as e:
        raise UserError(f'Failed to decompress Migaku data: {e}')


def _query_wordlist(sqlite_data: bytes) -> list[dict[str, Any]]:
    """Query the WordList table from the SQLite database."""
    # Write to temp file for sqlite3 to read
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp.write(sqlite_data)
        tmp_path = Path(tmp.name)

    try:
        conn = sqlite3.connect(str(tmp_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT dictForm, secondary, hasCard, mod, language, knownStatus ' 'FROM WordList WHERE del=0'
        )
        rows = cursor.fetchall()

        words = [dict(row) for row in rows]
        conn.close()
        return words

    except sqlite3.Error as e:
        raise UserError(f'Failed to read Migaku database: {e}')
    finally:
        tmp_path.remove()


def fetch_migaku_words_from_chrome(
    languages: list[str] | None = None,
) -> Generator[MigakuItem, None, None]:
    """Fetch Migaku words by reading Chrome's IndexedDB storage directly from disk."""
    chrome_path = _get_chrome_profile_path()
    pprint(f'Reading from Chrome data: "{chrome_path}"')

    blob_dir = _find_migaku_blob_path(chrome_path)
    pprint(f'Found Migaku data in: {blob_dir.parent.parent.name}')

    blob_path = _find_sqlite_blob(blob_dir)
    sqlite_data = _decompress_blob(blob_path)
    word_dicts = _query_wordlist(sqlite_data)

    if languages:
        word_dicts = [w for w in word_dicts if w.get('language') in languages]

    pprint(f'Extracted {len(word_dicts)} words from Migaku')
    for word_dict in word_dicts:
        yield MigakuItem.model_validate(word_dict)
