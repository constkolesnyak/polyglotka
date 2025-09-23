import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, Generator, List, Literal, Optional, Union

import icecream
from pydantic import BaseModel, Field
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

# Print the first item right from the file
# jq '.[0] | del(.audio, .context.phrase.subtitleTokens, .context.phrase.thumb_next, .context.phrase.thumb_prev)' lln_json_items_2025-9-23_part-1_645391.json


class WordForm(BaseModel):
    """Represents a word with its text and optional transliterations."""

    text: str
    translit: Optional[str] = None  # Korean, Thai, Japanese (kana)
    pinyin: Optional[List[str]] = None
    tones: Optional[List[int]] = None


class ItemAudio(BaseModel):
    """Audio data for saved items."""

    source: Literal['microsoft', 'google', 'movie']
    voice: Optional[str] = None
    output_format: str = Field(alias='outputFormat')  # e.g. 'Audio24Khz48KBitRateMonoMp3'
    date_created: int = Field(alias='dateCreated')  # unix timestamp
    data_url: str = Field(alias='dataURL')


class ThumbImage(BaseModel):
    """Thumbnail image data."""

    height: int
    width: int
    time: int
    data_url: str = Field(alias='dataURL')


class UdSingle(BaseModel):
    """Universal Dependencies single token data."""

    form: WordForm
    pos: Literal[
        'ADJ',
        'ADP',
        'ADV',
        'AUX',
        'NOUN',
        'PROPN',
        'VERB',
        'DET',
        'SYM',
        'INTJ',
        'CCONJ',
        'PUNCT',
        'X',
        'NUM',
        'PART',
        'PRON',
        'SCONJ',
        '_',
        'WS',
    ]
    index: Optional[int] = None
    lemma: Optional[WordForm] = None
    xpos: Optional[str] = None
    feats: Optional[Dict[str, Any]] = None  # Changed from 'features' to 'feats'
    pointer: Optional[int] = None
    deprel: Optional[str] = None
    freq: Optional[Union[int, str]] = None  # Can be int or "PUNCT_PLUS", "PROPN_PLUS"
    diocoFreq: Optional[Union[int, str]] = None
    form_norm: Optional[WordForm] = None


class YouTubeTmInfo(BaseModel):
    """YouTube tm information."""

    md5: Optional[str] = None
    name: Optional[str] = None
    vssId: Optional[str] = None
    isFromASR: Optional[bool] = None
    langCode_G: Optional[str] = None
    langCode_YT: Optional[str] = None
    isTranslatable: Optional[bool] = None
    isTranslatedTrack: Optional[bool] = None
    # Handle any additional fields that may be present
    id: Optional[str] = None
    audioDownloadableId: Optional[str] = None


class YouTubeReference(BaseModel):
    """Reference to YouTube video source."""

    source: Optional[str] = None  # Accept any string instead of literal
    tm: Optional[YouTubeTmInfo] = None  # Make optional
    savedFrom: Optional[str] = None
    diocoDocId: Optional[str] = None
    diocoDocName: Optional[str] = None
    endTime_ms: Optional[int] = None
    startTime_ms: Optional[int] = None
    subtitleIndex: Optional[int] = None
    refVersion: Optional[int] = None
    diocoPlaylistId: Optional[str] = None
    diocoPlaylistName: Optional[str] = None
    youtubeChannelId: Optional[str] = None
    youtubeChannelName: Optional[str] = None


class NetflixTmInfo(BaseModel):
    """Netflix tm information."""

    name: Optional[str] = None
    type: Optional[str] = None
    hydrated: Optional[Union[bool, str]] = None  # Can be bool or string
    audioType: Optional[str] = None
    langCode_G: Optional[str] = None
    langCode_N: Optional[str] = None
    contentHash: Optional[str] = None
    new_track_id: Optional[str] = None
    audioIsNative: Optional[bool] = None
    audioDownloadableId: Optional[str] = None
    # Handle any additional fields that may be present
    id: Optional[str] = None
    size: Optional[Union[int, str]] = None  # Can be int or string


class NetflixReference(BaseModel):
    """Reference to Netflix video source."""

    source: Optional[str] = None  # Accept any string instead of literal
    tm: Optional[NetflixTmInfo] = None  # Make optional
    packageId: Optional[str] = None
    title_arr: Optional[List[str]] = None
    diocoDocId: Optional[str] = None
    diocoDocName: Optional[str] = None
    endTime_ms: Optional[int] = None
    startTime_ms: Optional[int] = None
    subtitleIndex: Optional[int] = None
    refVersion: Optional[int] = None
    diocoPlaylistId: Optional[str] = None
    diocoPlaylistName: Optional[str] = None


class TextReference(BaseModel):
    """Reference to text source."""

    source: Optional[str] = None  # Accept any string instead of literal
    movie_id: Optional[str] = Field(default=None, alias='movieId')  # null if unsaved text
    title: Optional[str] = None
    tm: Optional[Dict[str, Any]] = None  # More flexible tm field
    url: Optional[str] = None


class VideoFileReference(BaseModel):
    """Reference to video file source."""

    source: Optional[str] = None  # Accept any string instead of literal
    movie_id: Optional[str] = Field(
        default=None, alias='movieId'
    )  # subs md5, used for querying
    title: Optional[str] = None  # file name, used for querying
    subtitle_index: Optional[int] = Field(default=None, alias='subtitleIndex')
    num_subs: Optional[int] = Field(default=None, alias='numSubs')
    start_time_ms: Optional[int] = Field(default=None, alias='startTime_ms')
    end_time_ms: Optional[int] = Field(default=None, alias='endTime_ms')
    tm: Optional[Dict[str, Any]] = None  # More flexible tm field


class DictionaryReference(BaseModel):
    """Reference to dictionary source."""

    source: Optional[str] = None  # Accept any string instead of literal
    tm: Optional[Dict[str, Any]] = None  # More flexible tm field
    title: Optional[str] = None
    movie_id: Optional[str] = Field(default=None, alias='movieId')


# Union of all reference types
Reference = Union[
    YouTubeReference,
    NetflixReference,
    TextReference,
    VideoFileReference,
    DictionaryReference,
]


class PhraseExport(BaseModel):
    """Phrase data for export."""

    subtitle_tokens: Dict[str, Optional[List[UdSingle]]] = Field(alias='subtitleTokens')
    subtitles: Dict[str, Optional[str]]
    m_translations: Optional[Dict[str, Optional[str]]] = Field(
        default=None, alias='mTranslations'
    )
    h_translations: Optional[Dict[str, Optional[str]]] = Field(
        default=None, alias='hTranslations'
    )
    reference: Reference
    thumb_prev: Optional[ThumbImage] = Field(default=None, alias='thumb_prev')
    thumb_next: Optional[ThumbImage] = Field(default=None, alias='thumb_next')


class SavedWordContext(BaseModel):
    """Context for saved words."""

    word_index: int = Field(alias='wordIndex')
    phrase: PhraseExport


class LearningStage(StrEnum):
    LEARNING = 'LEARNING'
    KNOWN = 'KNOWN'
    SKIPPED = 'SKIPPED'


class SavedWord(BaseModel):
    """Saved word item for export."""

    key: str
    item_type: Literal['WORD'] = Field(alias='itemType')
    lang_code_g: str = Field(alias='langCode_G')
    context: Optional[SavedWordContext] = None
    tags: List[str] = Field(default_factory=list)
    learning_stage: LearningStage = Field(alias='learningStage')
    word_translations_arr: Optional[List[str]] = Field(
        default=None, alias='wordTranslationsArr'
    )
    translation_lang_code_g: str = Field(alias='translationLangCode_G')
    word_type: Literal['lemma', 'form'] = Field(alias='wordType')
    word: WordForm
    time_modified_ms: int = Field(alias='timeModified_ms')
    time_created_ms: Optional[int] = Field(default=None, alias='timeCreated_ms')
    audio: Optional[ItemAudio] = None
    freq_rank: Optional[int] = Field(default=None, alias='freqRank')
    source: str
    review_data: Optional[Any] = Field(default=None, alias='reviewData')
    review_history: Optional[Any] = Field(default=None, alias='reviewHistory')
    dioco_freq: Optional[Union[int, str]] = Field(default=None, alias='diocoFreq')


class SavedPhraseContext(BaseModel):
    """Context for saved phrases."""

    phrase: PhraseExport


class SavedPhrase(BaseModel):
    """Saved phrase item for export."""

    key: str
    item_type: Literal['PHRASE'] = Field(alias='itemType')
    lang_code_g: str = Field(alias='langCode_G')
    translation_lang_code_g: str = Field(alias='translationLangCode_G')
    tags: List[str] = Field(default_factory=list)
    learning_stage: Literal['LEARNING', 'KNOWN', 'SKIPPED'] = Field(alias='learningStage')
    context: SavedPhraseContext
    time_modified_ms: int = Field(alias='timeModified_ms')
    time_created_ms: Optional[int] = Field(default=None, alias='timeCreated_ms')
    audio: Optional[ItemAudio] = None
    freq_rank: Optional[int] = Field(default=None, alias='freqRank')
    source: str
    review_data: Optional[Any] = Field(default=None, alias='reviewData')
    review_history: Optional[Any] = Field(default=None, alias='reviewHistory')
    dioco_freq: Optional[Union[int, str]] = Field(default=None, alias='diocoFreq')


# Union type for saved items
SavedItem = Union[SavedWord, SavedPhrase]


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
        print(f"Warning: Failed to parse item as SavedItem: {e}")
        print(
            f"Item data keys: {list(item_data.keys()) if isinstance(item_data, dict) else 'Not a dict'}"  # pyright: ignore
        )
        return None


def read_lr_data(
    data_directory: str, progress: Progress
) -> Generator[SavedItem, None, None]:
    """Read LR data from JSON files.

    Args:
        data_directory: Directory containing JSON files
        progress: Rich progress bar instance

    Yields:
        SavedItem objects (SavedWord or SavedPhrase)
    """
    data_path = Path(data_directory)

    if not data_path.exists():
        raise FileNotFoundError(f'Directory not found: {data_directory}')

    json_files = list(data_path.glob('lln_json_items_*.json'))
    if not json_files:
        raise FileNotFoundError(f'No JSON files found in directory: {data_directory}')

    with progress:
        progress_task = progress.add_task('Processing files...', total=len(json_files))

        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                items: list[Any] = json.load(f)

            for item in items:
                saved_item: SavedWord | SavedPhrase | None = parse_saved_item(item)
                assert saved_item
                yield saved_item

            progress.update(progress_task, advance=1)


# tdc VVV move to tests


def display_saved_word(word: SavedWord, item_num: int) -> None:
    """Display detailed information about a SavedWord."""
    print(f'\n=== SavedWord #{item_num} ===')
    print(f'Text: {word.word.text}')
    if word.word.translit:
        print(f'Transliteration: {word.word.translit}')
    if word.word.pinyin:
        print(f'Pinyin: {", ".join(word.word.pinyin)}')
    if word.word.tones:
        print(f'Tones: {word.word.tones}')

    print(f'Language: {word.lang_code_g}')
    print(f'Translation Language: {word.translation_lang_code_g}')
    print(f'Word Type: {word.word_type}')
    print(f'Learning Stage: {word.learning_stage}')
    print(f'Frequency Rank: {word.freq_rank}')

    if word.word_translations_arr:
        print(f'Translations: {", ".join(word.word_translations_arr)}')

    if word.tags:
        print(f'Tags: {", ".join(word.tags)}')

    if word.context:
        print(f'Context - Word Index: {word.context.word_index}')
        reference = word.context.phrase.reference
        print(f'Context - Source: {reference.source}')

    print(f'Modified: {datetime.fromtimestamp(word.time_modified_ms / 1000)}')


def display_saved_phrase(phrase: SavedPhrase, item_num: int) -> None:
    """Display detailed information about a SavedPhrase."""
    print(f'\n=== SavedPhrase #{item_num} ===')

    # Get the main subtitle text
    subtitles = phrase.context.phrase.subtitles
    main_text = subtitles.get('1', '') or next(iter(subtitles.values()), '')
    print(f'Text: {main_text}')

    print(f'Language: {phrase.lang_code_g}')
    print(f'Translation Language: {phrase.translation_lang_code_g}')
    print(f'Learning Stage: {phrase.learning_stage}')
    print(f'Frequency Rank: {phrase.freq_rank}')

    if phrase.tags:
        print(f'Tags: {", ".join(phrase.tags)}')

    # Show all subtitles
    print('Subtitles:')
    for key, text in subtitles.items():
        if text:
            print(f'  [{key}]: {text}')

    # Show translations if available
    if phrase.context.phrase.m_translations:
        print('Machine Translations:')
        for key, translation in phrase.context.phrase.m_translations.items():
            if translation:
                print(f'  [{key}]: {translation}')

    if phrase.context.phrase.h_translations:
        print('Human Translations:')
        for key, translation in phrase.context.phrase.h_translations.items():
            if translation:
                print(f'  [{key}]: {translation}')

    # Show reference information
    reference = phrase.context.phrase.reference
    print(f'Source: {reference.source}')
    print(f'Modified: {datetime.fromtimestamp(phrase.time_modified_ms / 1000)}')


def main(max_display: int = 5) -> None:
    """Main function to process and display language learning data.

    Args:
        max_display: Maximum number of items to display in detail
    """
    console = Console()
    progress = Progress(
        SpinnerColumn(style='bright_magenta'),
        BarColumn(complete_style='bright_magenta'),
        TextColumn('[bright_magenta]•'),
        TextColumn('[bright_magenta]{task.completed:,} / {task.total:,} files processed'),
        console=console,
        transient=True,
    )
    data_dir = '/Users/konst/Downloads'

    print(f"Reading data with full SavedItem models...")
    print(f"Will display first {max_display} items in detail.")

    total_items = 0
    word_count = 0
    phrase_count = 0

    try:
        for item in read_lr_data(data_dir, progress):
            total_items += 1

            if total_items <= max_display:
                if isinstance(item, SavedWord):
                    word_count += 1
                    display_saved_word(item, total_items)
                elif isinstance(item, SavedPhrase):
                    phrase_count += 1
                    display_saved_phrase(item, total_items)
            else:
                # Just count item types for summary
                if isinstance(item, SavedWord):
                    word_count += 1
                elif isinstance(item, SavedPhrase):
                    phrase_count += 1

    except Exception as e:
        print(f"\nError during processing: {e}")
        return

    print(f'\n=== Final Summary ===')
    print(f'Total items processed: {total_items:,}')
    print(f'Words: {word_count:,}')
    print(f'Phrases: {phrase_count:,}')
    print(f'Other/Unknown: {total_items - word_count - phrase_count:,}')


if __name__ == "__main__":
    main()


# Keep original functions for backward compatibility
def create_trig_data() -> dict[str, list[float]]:
    x = [i * 0.1 for i in range(100)]
    return {
        'x': x,
        'sin_x': [math.sin(val) for val in x],
        'cos_x': [math.cos(val) for val in x],
        'sin_2x': [math.sin(2 * val) for val in x],
        'cos_2x': [math.cos(2 * val) for val in x],
    }
