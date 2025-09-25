import json
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, Generator, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from polyglotka.common.config import config
from polyglotka.common.console import Progress, ProgressType

# You also can print the first item straight from the json file:
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
    movie_id: Optional[str] = Field(default=None, alias='movieId')  # subs md5, used for querying
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
    m_translations: Optional[Dict[str, Optional[str]]] = Field(default=None, alias='mTranslations')
    h_translations: Optional[Dict[str, Optional[str]]] = Field(default=None, alias='hTranslations')
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
    word_translations_arr: Optional[List[str]] = Field(default=None, alias='wordTranslationsArr')
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


def import_lr_items() -> Generator[SavedItem, None, None]:
    lr_data_dir = Path(config.LR_DATA_DIR)

    if not lr_data_dir.exists():
        raise FileNotFoundError(f'Directory not found: {lr_data_dir}')

    json_files = list(lr_data_dir.glob('lln_json_items_*.json'))
    if not json_files:
        raise FileNotFoundError(f'No JSON files found in directory: {lr_data_dir}')

    with Progress(
        ProgressType.BAR,
        'Importing LR data',
        'files',
        total_tasks=len(json_files),
    ) as progress:
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                items: list[Any] = json.load(f)

            for item in items:
                saved_item: SavedWord | SavedPhrase | None = parse_saved_item(item)
                assert saved_item
                yield saved_item

            progress.update(advance=1)
