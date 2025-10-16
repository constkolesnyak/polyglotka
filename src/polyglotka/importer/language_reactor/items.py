import json
from typing import Any, Dict, Generator, Optional

from path import Path

from polyglotka.common.config import config
from polyglotka.common.console import Progress, ProgressType
from polyglotka.common.exceptions import UserError
from polyglotka.importer.language_reactor.structures import (
    SavedItem,
    SavedPhrase,
    SavedWord,
)


def parse_saved_item(item_data: Dict[str, Any]) -> Optional[SavedItem]:
    """Parse a raw JSON item into a SavedItem (SavedWord or SavedPhrase)."""
    try:
        item_type = item_data.get('itemType')
        if item_type == 'WORD':
            return SavedWord(**item_data)
        elif item_type == 'PHRASE':
            return SavedPhrase(**item_data)
        else:
            print(f"Warning: Unknown item type '{item_type}', skipping item")
            return None
    except Exception as e:
        print(f'Warning: Failed to parse item as SavedItem: {e}')
        print(
            f"Item data keys: {list(item_data.keys()) if isinstance(item_data, dict) else 'Not a dict'}"  # pyright: ignore
        )
        return None


def import_lr_items() -> Generator[SavedItem, None, None]:
    lr_files: list[Path] = Path(config.LR_DATA_DIR).glob(config.LR_DATA_FILES_GLOB_PATTERN)

    with Progress(
        progress_type=ProgressType.BAR,
        text='Importing LR data',
        postfix='files',
        total_tasks=len(lr_files),
    ) as progress:
        for lr_file in lr_files:
            for item in json.loads(lr_file.read_text()):
                saved_item: SavedWord | SavedPhrase | None = parse_saved_item(item)
                assert saved_item
                yield saved_item
            progress.update(advance=1)
