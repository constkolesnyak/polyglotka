"""Direct Language Reactor import by reading Chrome's IndexedDB auth blob and
calling the Language Reactor backend API.

Flow:
  1. Copy the LR extension's IndexedDB leveldb out of the live Chrome profile.
  2. Parse the `firebase:authUser:*` record to get refresh_token + apiKey.
  3. Exchange refresh_token for a Firebase id_token (securetoken.googleapis.com).
  4. Call the `getUserData_3` Cloud Function to mint a short-lived diocoToken.
  5. Page through `base_items_getItems_5` on api-cdn.dioco.io to fetch all saved items.
"""

import pathlib
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Generator

import requests
from path import Path

from polyglotka.common.chrome import CHROME_PROFILE_NAMES, get_chrome_profile_path
from polyglotka.common.console import Progress, ProgressType, pprint
from polyglotka.common.exceptions import UserError
from polyglotka.importer.language_reactor.importer import parse_saved_item
from polyglotka.importer.language_reactor.structures import LRSavedItem

LR_EXTENSION_ID = 'hoombieeljmmljlkjmnheibnpciblicm'
LR_IDB_DIR_NAME = f'chrome-extension_{LR_EXTENSION_ID}_0.indexeddb.leveldb'
LR_BLOB_DIR_NAME = f'chrome-extension_{LR_EXTENSION_ID}_0.indexeddb.blob'

FIREBASE_PROJECT_ID = 'nlle-b0128'
FIREBASE_REGION = 'us-central1'
SECURETOKEN_URL = 'https://securetoken.googleapis.com/v1/token'
CLOUD_FUNCTION_URL = (
    f'https://{FIREBASE_REGION}-{FIREBASE_PROJECT_ID}.cloudfunctions.net/getUserData_3'
)
DIOCO_API_BASE = 'https://api-cdn.dioco.io'
GET_ITEMS_PATH = '/base_items_getItems_5'
GET_ITEM_KEYS_PATH = '/base_items_getItemKeys_3'

# Page size tuned empirically: ~200 items = ~2MB response, ~100s server time.
# Smaller batches hammer HTTP overhead, larger ones trigger server-side truncation.
PAGE_SIZE = 200
REQUEST_TIMEOUT_S = 300
USER_AGENT = 'polyglotka/lr-import'
# Probed dioco cap: N=4 inflates per-request latency, N>4 risks 429.
LR_MAX_WORKERS = 3


def _find_lr_leveldb_path(chrome_path: Path) -> Path:
    """Find the LR extension's IndexedDB leveldb directory."""
    for profile_name in CHROME_PROFILE_NAMES:
        leveldb = chrome_path / profile_name / 'IndexedDB' / LR_IDB_DIR_NAME
        if leveldb.exists():
            return leveldb

    for profile_dir in chrome_path.dirs():
        leveldb = profile_dir / 'IndexedDB' / LR_IDB_DIR_NAME
        if leveldb.exists():
            return leveldb

    raise UserError(
        'Language Reactor data not found in any Chrome profile.\n'
        'Please make sure the Language Reactor extension is installed and you are '
        'signed in at https://www.languagereactor.com in Chrome.'
    )


def _copy_leveldb_to_tempdir(leveldb_path: Path) -> Path:
    """Copy the leveldb directory to a temp location so we can read it safely while
    Chrome holds a file lock on the live copy. Also creates an empty sibling `.blob`
    directory because dfindexeddb's `db` parser insists it exists."""
    tmp_root = Path(tempfile.mkdtemp(prefix='polyglotka-lr-idb-'))
    dest = tmp_root / LR_IDB_DIR_NAME
    shutil.copytree(str(leveldb_path), str(dest))
    lock = dest / 'LOCK'
    if lock.exists():
        lock.remove()
    (tmp_root / LR_BLOB_DIR_NAME).makedirs_p()
    return dest


def _parse_firebase_auth(leveldb_path: Path) -> dict[str, str]:
    """Extract the firebase:authUser record from the copied leveldb."""
    try:
        from dfindexeddb.indexeddb.chromium.record import FolderReader
    except ImportError as e:
        raise UserError(
            'The `dfindexeddb` package is required for Language Reactor Chrome import.\n'
            f'Install it with: uv sync  ({e})'
        )

    reader = FolderReader(pathlib.Path(str(leveldb_path)))
    for record in reader.GetRecords():
        wrapper = getattr(record, 'value', None)
        value = getattr(wrapper, 'value', None) if wrapper is not None else None
        if not isinstance(value, dict):
            continue
        fbase_key = value.get('fbase_key', '')
        if not fbase_key.startswith('firebase:authUser:'):
            continue
        inner = value.get('value')
        if not isinstance(inner, dict):
            continue
        sts = inner.get('stsTokenManager') or {}
        refresh_token = sts.get('refreshToken')
        api_key = inner.get('apiKey')
        uid = inner.get('uid')
        email = inner.get('email')
        if not (refresh_token and api_key and uid):
            raise UserError(
                'Found a firebase:authUser record, but stsTokenManager/apiKey/uid fields were empty. '
                'Try signing out and back into Language Reactor in Chrome.'
            )
        return {
            'refresh_token': refresh_token,
            'api_key': api_key,
            'uid': uid,
            'email': email or '',
        }

    raise UserError(
        'No firebase:authUser record found in the Language Reactor IndexedDB.\n'
        'Please sign in to Language Reactor in Chrome and try again.'
    )


def _refresh_id_token(refresh_token: str, api_key: str) -> str:
    """Exchange a Firebase refresh token for a fresh id_token."""
    response = requests.post(
        f'{SECURETOKEN_URL}?key={api_key}',
        data={'grant_type': 'refresh_token', 'refresh_token': refresh_token},
        headers={'User-Agent': USER_AGENT},
        timeout=30,
    )
    if response.status_code != 200:
        raise UserError(
            f'Failed to refresh Firebase id_token ({response.status_code}): {response.text[:300]}'
        )
    payload = response.json()
    id_token = payload.get('id_token')
    if not id_token:
        raise UserError(f'Firebase refresh response missing id_token: {payload}')
    return id_token


def _mint_dioco_token(id_token: str) -> tuple[str, str]:
    """Call the `getUserData_3` Firebase Cloud Function (httpsCallable wire format)
    and return (diocoToken, googleEmail)."""
    response = requests.post(
        CLOUD_FUNCTION_URL,
        headers={
            'Authorization': f'Bearer {id_token}',
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT,
        },
        json={'data': {}},
        timeout=60,
    )
    if response.status_code != 200:
        raise UserError(
            f'Language Reactor getUserData_3 failed ({response.status_code}): {response.text[:500]}'
        )
    user_data = response.json().get('result') or {}
    dioco_token = user_data.get('diocoToken')
    google_email = user_data.get('googleEmail')
    if not (dioco_token and google_email):
        raise UserError(
            'Language Reactor did not return a diocoToken/googleEmail. '
            'Your account may not be fully set up; try opening languagereactor.com first.'
        )
    return dioco_token, google_email


def _build_query(google_email: str, num_results: int, offset: int) -> dict[str, Any]:
    """Build the `query` object expected by base_items_getItems_5. All fields are
    required by the server-side validator even when null."""
    return {
        'userEmail': google_email,
        'tags': None,
        'learningStages': None,
        'itemType': None,
        'langCode_G': None,
        'toTimestamp': None,
        'fromTimestamp': None,
        'orderBy': 'TIME_MODIFIED_DESC',
        'toExtendedKey': None,
        'numResults': num_results,
        'offset': offset,
        'wordKey': None,
        'source': None,
        'title': None,
        'itemKeys': None,
        'searchText': None,
    }


def _count_saved_items(dioco_token: str, google_email: str) -> int:
    """Call getItemKeys_3 (cheap, ~1s) to learn how many items we're about to fetch.
    The response is a nested tree keyed by lang -> WORD/PHRASE -> learningStage -> lemma;
    we just count the leaves."""
    response = requests.post(
        f'{DIOCO_API_BASE}{GET_ITEM_KEYS_PATH}',
        headers={'Content-Type': 'application/json', 'User-Agent': USER_AGENT},
        json={'diocoToken': dioco_token, 'userEmail': google_email},
        timeout=60,
    )
    if response.status_code != 200 or response.json().get('status') != 'success':
        return 0
    tree = (((response.json().get('data') or {}).get('itemKeys') or {}).get('itemKeys')) or {}
    total = 0
    for lang_bucket in tree.values():
        if not isinstance(lang_bucket, dict):
            continue
        for kind_bucket in lang_bucket.values():
            if not isinstance(kind_bucket, dict):
                continue
            for lemmas in kind_bucket.values():
                if isinstance(lemmas, dict):
                    total += len(lemmas)
    return total


def _fetch_page(dioco_token: str, google_email: str, offset: int) -> list[dict[str, Any]]:
    response = requests.post(
        f'{DIOCO_API_BASE}{GET_ITEMS_PATH}',
        headers={'Content-Type': 'application/json', 'User-Agent': USER_AGENT},
        json={
            'diocoToken': dioco_token,
            'query': _build_query(google_email, PAGE_SIZE, offset),
        },
        timeout=REQUEST_TIMEOUT_S,
    )
    if response.status_code != 200:
        raise UserError(
            f'Language Reactor getItems_5 failed at offset={offset} '
            f'({response.status_code}): {response.text[:300]}'
        )
    payload = response.json()
    if payload.get('status') != 'success':
        raise UserError(
            f'Language Reactor getItems_5 returned error at offset={offset}: {payload.get("error")}'
        )
    data = payload.get('data') or {}
    items = data.get('items') or []
    return items


def _fetch_all_items_parallel(
    dioco_token: str,
    google_email: str,
    expected_total: int,
    progress,
) -> Generator[dict[str, Any], None, None]:
    """Fire all offsets concurrently with a bounded pool. Yields raw item dicts
    in page-arrival order."""
    offsets = list(range(0, expected_total, PAGE_SIZE))
    with ThreadPoolExecutor(max_workers=LR_MAX_WORKERS) as pool:
        futures = {
            pool.submit(_fetch_page, dioco_token, google_email, offset): offset
            for offset in offsets
        }
        for future in as_completed(futures):
            page = future.result()
            for raw_item in page:
                yield raw_item
            progress.update(advance=len(page))


def _fetch_all_items_sequential(
    dioco_token: str,
    google_email: str,
    progress,
) -> Generator[dict[str, Any], None, None]:
    """Fallback when total is unknown up-front. Stops on short page."""
    offset = 0
    while True:
        page = _fetch_page(dioco_token, google_email, offset)
        if not page:
            break
        for raw_item in page:
            yield raw_item
        progress.update(advance=len(page))
        if len(page) < PAGE_SIZE:
            break
        offset += len(page)


def fetch_lr_items_from_chrome() -> Generator[LRSavedItem, None, None]:
    """Top-level generator: yields LRSavedItem objects fetched live from Language
    Reactor's backend using credentials pulled from the local Chrome profile."""
    chrome_path = get_chrome_profile_path()
    pprint(f'Reading Chrome data from: "{chrome_path}"')

    live_leveldb = _find_lr_leveldb_path(chrome_path)
    pprint(f'Found Language Reactor data in: {live_leveldb.parent.parent.name}')

    tmp_leveldb = _copy_leveldb_to_tempdir(live_leveldb)
    try:
        auth = _parse_firebase_auth(tmp_leveldb)
    finally:
        shutil.rmtree(str(tmp_leveldb.parent), ignore_errors=True)

    pprint(f'Authenticating as: {auth["email"] or auth["uid"]}')
    id_token = _refresh_id_token(auth['refresh_token'], auth['api_key'])
    dioco_token, google_email = _mint_dioco_token(id_token)

    expected_total = _count_saved_items(dioco_token, google_email)
    if expected_total:
        pprint(f'Fetching {expected_total} saved items from Language Reactor...')
    else:
        pprint('Fetching saved items from Language Reactor...')

    total_yielded = 0
    with Progress(
        progress_type=ProgressType.BAR,
        text='Importing LR data (from Chrome)',
        postfix='items',
        total_tasks=expected_total or None,
    ) as progress:
        if expected_total:
            raw_stream = _fetch_all_items_parallel(
                dioco_token, google_email, expected_total, progress
            )
        else:
            raw_stream = _fetch_all_items_sequential(dioco_token, google_email, progress)

        for raw_item in raw_stream:
            parsed = parse_saved_item(raw_item)
            if parsed is not None:
                yield parsed
                total_yielded += 1

    pprint(f'Extracted {total_yielded} items from Language Reactor')
