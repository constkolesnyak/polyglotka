import json
from typing import Any, Dict, Generator, Optional

from path import Path

from polyglotka.common.console import Progress, ProgressType
from polyglotka.importer.language_reactor.structures import (
    LRSavedItem,
    LRSavedPhrase,
    LRSavedWord,
)


def parse_saved_item(item_data: Dict[str, Any]) -> Optional[LRSavedItem]:
    """Parse a raw JSON item into a SavedItem (SavedWord or SavedPhrase)."""
    try:
        item_type = item_data.get('itemType')
        if item_type == 'WORD':
            return LRSavedWord(**item_data)
        elif item_type == 'PHRASE':
            return LRSavedPhrase(**item_data)
        else:
            print(f"Warning: Unknown item type '{item_type}', skipping item")
            return None
    except Exception as e:
        print(f'Warning: Failed to parse item as SavedItem: {e}')
        print(
            f"Item data keys: {list(item_data.keys()) if isinstance(item_data, dict) else 'Not a dict'}"  # pyright: ignore
        )
        return None


def import_lr_items(lr_files: list[Path]) -> Generator[LRSavedItem, None, None]:
    if not lr_files:
        return
    with Progress(
        progress_type=ProgressType.BAR,
        text='Importing LR data',
        postfix='files',
        total_tasks=len(lr_files),
    ) as progress:
        for lr_file in lr_files:
            for item in json.loads(lr_file.read_text()):
                saved_item: LRSavedWord | LRSavedPhrase | None = parse_saved_item(item)
                assert saved_item
                yield saved_item
            progress.update(advance=1)
