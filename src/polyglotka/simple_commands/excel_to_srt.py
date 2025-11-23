import re
from dataclasses import dataclass
from typing import Optional, Sequence

import icecream
import pandas as pd
from path import Path

from polyglotka.common.config import config
from polyglotka.common.console import pprint
from polyglotka.common.exceptions import UserError
from polyglotka.common.utils import remove_files_maybe


@dataclass(frozen=True)
class SubtitleSegment:
    start_ms: int
    end_ms: int


def parse_time(value: str | None) -> Optional[int]:
    """Parse a timestamp into milliseconds; return None for missing data."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    time_str = str(value).strip()
    if not time_str:
        return None

    if time_str.endswith('s'):
        return int(float(time_str[:-1]) * 1000)

    parts = time_str.split(':')
    try:
        if len(parts) == 2:
            minutes, seconds = parts
            return int((int(minutes) * 60 + float(seconds)) * 1000)
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1000)
    except ValueError as exc:
        raise ValueError(f'Invalid time format: {time_str}') from exc

    raise ValueError(f'Invalid time format: {time_str}')


def ms_to_srt(ms: int) -> str:
    hours, remainder = divmod(ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}'


def estimate_end(start_ms: int, text: str, next_start_ms: Optional[int]) -> int:
    """Estimate an end timestamp using a reading-speed heuristic.

    The result is always within ``[start_ms, next_start_ms)`` when the next
    timestamp exists, with a small configurable gap to avoid overlaps.
    """

    MIN_DURATION_MS = 1000
    MAX_DURATION_MS = 9**9
    BASE_DURATION_MS = 400
    GAP_BETWEEN_SEGMENTS_MS = 50

    readable_chars = len(_strip_newlines(text))
    duration_ms = BASE_DURATION_MS + readable_chars * config.LR_SUBS_MS_PER_CHAR
    duration_ms = max(MIN_DURATION_MS, min(duration_ms, MAX_DURATION_MS))

    proposed_end = start_ms + duration_ms
    if next_start_ms is None:
        return proposed_end

    latest_allowed = max(start_ms, next_start_ms - GAP_BETWEEN_SEGMENTS_MS)
    if latest_allowed <= start_ms:
        return start_ms

    return min(proposed_end, latest_allowed)


def build_segments(
    times_ms: Sequence[Optional[int]],
    primary_texts: Sequence[str],
    secondary_texts: Optional[Sequence[str]] = None,
) -> list[Optional[SubtitleSegment]]:
    """Compute shared (start, end) pairs for all rows."""

    next_starts = _compute_next_starts(times_ms)
    segments: list[Optional[SubtitleSegment]] = []

    for idx, start_ms in enumerate(times_ms):
        if start_ms is None:
            segments.append(None)
            continue

        text = _normalise_text(primary_texts[idx])
        if not text and secondary_texts is not None:
            text = _normalise_text(secondary_texts[idx])

        end_ms = estimate_end(start_ms, text, next_starts[idx])
        segments.append(SubtitleSegment(start_ms=start_ms, end_ms=end_ms))

    return segments


def create_srt_text(segments: Sequence[Optional[SubtitleSegment]], texts: Sequence[str]) -> str:
    """Render the SRT file using pre-computed aligned segments."""

    lines: list[str] = []
    counter = 1
    for segment, raw_text in zip(segments, texts):
        if segment is None:
            continue
        text = _normalise_text(raw_text)
        if not text:
            continue

        lines.append(str(counter))
        lines.append(f'{ms_to_srt(segment.start_ms)} --> {ms_to_srt(segment.end_ms)}')
        lines.extend(text.splitlines())
        lines.append('')
        counter += 1

    return '\n'.join(lines)


def _normalise_text(value: str | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ''
    return str(value).strip()


def _strip_newlines(text: str) -> str:
    return text.replace('\n', ' ').strip()


def _compute_next_starts(times_ms: Sequence[Optional[int]]) -> list[Optional[int]]:
    next_starts: list[Optional[int]] = [None] * len(times_ms)
    next_start: Optional[int] = None
    for idx in range(len(times_ms) - 1, -1, -1):
        next_starts[idx] = next_start
        current = times_ms[idx]
        if current is not None:
            next_start = current
    return next_starts


def create_srt_name(lr_subs_file: str, episode: int) -> str:
    name: str = Path(lr_subs_file).stem.split('_')[-1]

    if config.NAME:
        name = config.NAME
    if episode:
        if not config.NAME:
            raise UserError('NAME must be provided for multiple LR subs files')
        name += f'_{episode}'

    return name


def create_srt_file(srt_path: Path, srt_text: str) -> None:
    srt_path.write_text(srt_text, encoding='utf-8')
    pprint(f'Added "{srt_path}".')


def convert_excel_to_srt(lr_subs_file: str, srt_name: str) -> None:
    dataframe: pd.DataFrame = pd.read_excel(Path(lr_subs_file))  # type: ignore

    times_ms: list[int | None] = [parse_time(value) for value in dataframe['Time']]
    primary_texts: list[str] = dataframe['Subtitle'].tolist()
    secondary_texts: list[str] | None = (
        dataframe['Machine Translation'].tolist() if 'Machine Translation' in dataframe.columns else None
    )

    segments: list[SubtitleSegment | None] = build_segments(times_ms, primary_texts, secondary_texts)

    if secondary_texts is not None:
        create_srt_file(
            Path(config.SRT_SUBS_TARGET_DIR) / f'{srt_name}_secondary.srt',
            create_srt_text(segments, secondary_texts),
        )
    create_srt_file(
        Path(config.SRT_SUBS_TARGET_DIR) / f'{srt_name}_primary.srt',
        create_srt_text(segments, primary_texts),
    )


def trash_existing_srt_files() -> None:
    pattern = re.compile(r'^\d+_(?:primary|secondary)\.srt$')
    target_dir = Path(config.SRT_SUBS_TARGET_DIR)
    trash_dir = Path(config.SRT_SUBS_TRASH_DIR).mkdir_p()

    for srt_file in target_dir.glob('*.srt'):
        if srt_file.is_file() and pattern.fullmatch(srt_file.name):
            new_path = trash_dir / srt_file.name
            srt_file.move(new_path)
            pprint(f'Trashed "{new_path}".')


def main() -> None:
    if lr_subs_files := Path(config.EXPORTED_FILES_DIR).glob(config.LR_SUBS_GLOB_PATTERN):
        trash_existing_srt_files()

        episode_start = 0 if len(lr_subs_files) == 1 else config.START
        sorted_lr_subs_files = sorted(lr_subs_files, key=lambda file: file.getmtime())

        for episode, lr_subs_file in enumerate(sorted_lr_subs_files, episode_start):
            srt_name = create_srt_name(lr_subs_file, episode)
            convert_excel_to_srt(lr_subs_file, srt_name)
        remove_files_maybe(lr_subs_files)
