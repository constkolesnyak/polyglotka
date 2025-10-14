#!/usr/bin/env python3
"""Convert Excel exports to aligned SRT subtitle/translation tracks."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

MIN_DURATION_MS = 1000
MAX_DURATION_MS = 6000
BASE_DURATION_MS = 400
MS_PER_CHAR = 65
GAP_BETWEEN_SEGMENTS_MS = 100


@dataclass(frozen=True)
class SubtitleSegment:
    start_ms: int
    end_ms: int


def parse_time(value: object) -> Optional[int]:
    """Parse a timestamp into milliseconds; return None for missing data."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    time_str = str(value).strip()
    if not time_str:
        return None

    if time_str.endswith("s"):
        return int(float(time_str[:-1]) * 1000)

    parts = time_str.split(":")
    try:
        if len(parts) == 2:
            minutes, seconds = parts
            return int((int(minutes) * 60 + float(seconds)) * 1000)
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1000)
    except ValueError as exc:  # fall through to error message
        raise ValueError(f"Invalid time format: {time_str}") from exc

    raise ValueError(f"Invalid time format: {time_str}")


def ms_to_srt(ms: int) -> str:
    hours, remainder = divmod(ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def estimate_end(start_ms: int, text: str, next_start_ms: Optional[int]) -> int:
    """Estimate an end timestamp using a reading-speed heuristic.

    The result is always within ``[start_ms, next_start_ms)`` when the next
    timestamp exists, with a small configurable gap to avoid overlaps.
    """

    readable_chars = len(_strip_newlines(text))
    duration_ms = BASE_DURATION_MS + readable_chars * MS_PER_CHAR
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


def create_srt(
    segments: Sequence[Optional[SubtitleSegment]],
    texts: Sequence[str],
    output_path: Path,
) -> int:
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
        lines.append(f"{ms_to_srt(segment.start_ms)} --> {ms_to_srt(segment.end_ms)}")
        lines.extend(text.splitlines())
        lines.append("")
        counter += 1

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return counter - 1


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python excel_to_srt.py <input.xlsx>")
        sys.exit(1)

    excel_path = Path(sys.argv[1])
    df = pd.read_excel(excel_path)

    try:
        times_ms = [parse_time(value) for value in df["Time"]]
    except KeyError as exc:
        raise SystemExit("Missing required 'Time' column") from exc

    try:
        primary_texts = df["Subtitle"].tolist()
    except KeyError as exc:
        raise SystemExit("Missing required 'Subtitle' column") from exc

    secondary_texts = df["Machine Translation"].tolist() if "Machine Translation" in df.columns else None
    segments = build_segments(times_ms, primary_texts, secondary_texts)

    subtitle_path = excel_path.with_name(f"{excel_path.stem}_subtitles.srt")
    subtitle_count = create_srt(segments, primary_texts, subtitle_path)
    print(f"Created {subtitle_path} with {subtitle_count} subtitles")

    if secondary_texts is not None:
        translation_path = excel_path.with_name(f"{excel_path.stem}_translations.srt")
        translation_count = create_srt(segments, secondary_texts, translation_path)
        print(f"Created {translation_path} with {translation_count} subtitles")
    else:
        print("No 'Machine Translation' column found")


def _normalise_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _strip_newlines(text: str) -> str:
    return text.replace("\n", " ").strip()


def _compute_next_starts(times_ms: Sequence[Optional[int]]) -> list[Optional[int]]:
    next_starts: list[Optional[int]] = [None] * len(times_ms)
    next_start: Optional[int] = None
    for idx in range(len(times_ms) - 1, -1, -1):
        next_starts[idx] = next_start
        current = times_ms[idx]
        if current is not None:
            next_start = current
    return next_starts


if __name__ == "__main__":
    main()
