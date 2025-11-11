from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go  # pyright: ignore
from funcy import pluck_attr  # pyright: ignore

from polyglotka.common.config import config
from polyglotka.importer.words import LearningStage, Word
from polyglotka.plots.appearance import configure_figure, get_color

ALL = 'ALL'  # all langs or all learning stages


class WordDicts:
    def __init__(self, words: Iterable[Word]) -> None:
        self.all_words = set(words)
        self.by_lang: defaultdict[str, set[Word]] = defaultdict(set)
        self.by_stage: defaultdict[LearningStage, set[Word]] = defaultdict(set)
        self.by_lang_stage: defaultdict[
            tuple[str, LearningStage],
            set[Word],
        ] = defaultdict(set)

        for word in self.all_words:
            self.by_lang[word.language].add(word)
            self.by_stage[word.learning_stage].add(word)
            self.by_lang_stage[(word.language, word.learning_stage)].add(word)


def create_points(words: Iterable[Word]) -> tuple[list[datetime], list[int]]:
    word_dates: list[datetime] = sorted(pluck_attr('date', words))
    # Start 1 hour before first word to show initial bursts as vertical jumps
    start = word_dates[0].replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    end = word_dates[-1]
    hourly_points = [
        start + timedelta(hours=i) for i in range(int((end - start).total_seconds() // 3600) + 1)
    ]
    x_data: list[datetime] = sorted(set(word_dates + hourly_points))
    y_data: list[int] = [sum(1 for wd in word_dates if wd <= x) for x in x_data]

    if config.PLOTS_SMOOTH:
        series = pd.Series(y_data, index=pd.to_datetime(x_data)).sort_index()
        rate = series.diff().fillna(0).resample('h').sum()  # type: ignore

        # Detect burst periods: hours with >50 words for this specific trace
        burst_threshold = 50
        is_burst = rate > burst_threshold

        # Reset smoothing at burst boundaries to prevent tails
        rate_smooth = pd.Series(0.0, index=rate.index)
        for i in range(len(rate)):
            if is_burst.iloc[i]:
                rate_smooth.iloc[i] = 0  # Bursts get no smoothing
            elif i > 0 and not is_burst.iloc[i - 1]:
                # Continue smoothing from previous non-burst hour
                alpha = 2 / (6 * 2 + 1)  # halflife=6 converted to alpha
                rate_smooth.iloc[i] = alpha * rate.iloc[i] + (1 - alpha) * rate_smooth.iloc[i - 1]
            else:
                # First hour or hour after burst: start fresh
                rate_smooth.iloc[i] = rate.iloc[i]

        # Add back bursts at their original positions (creates vertical jumps)
        rate_final = rate_smooth.copy()
        rate_final[is_burst] = rate[is_burst]

        # Reconstruct cumulative curve
        y_smooth = rate_final.cumsum()
        y_smooth *= series.iloc[-1] / y_smooth.iloc[-1]
        x_data, y_data = y_smooth.index, y_smooth.values.round().astype(int).tolist()  # type: ignore

    return x_data, y_data  # type: ignore


def create_trace(
    language: str,
    learning_stage: str,
    words: Iterable[Word],
) -> go.Scatter:
    words = list(words)
    if not words:
        return go.Scatter(name='')

    x_data, y_data = create_points(words)
    name = f'{language.upper()} - {learning_stage.capitalize()}'

    line_width = 3
    visible = True
    if ALL in name.upper():
        line_width = 4
        if config.PLOTS_HIDE_AGGR:
            visible = False
    if LearningStage.LEARNING == learning_stage and config.PLOTS_HIDE_LEARNING:
        visible = False

    if config.PLOTS_HIDE_AGGR and config.PLOTS_HIDE_LEARNING:
        name = language.upper()

    return go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines',
        name=name,
        line=dict(
            color=get_color(language, learning_stage),
            width=line_width,
        ),
        visible=visible,
    )


def create_figure(words: Iterable[Word]) -> go.Figure:
    wds = WordDicts(words)
    fig: go.Figure = go.Figure()
    languages = wds.by_lang.keys()
    stages = wds.by_stage.keys()
    traces: list[go.Scatter] = []

    for lang in languages:
        for stage in stages:
            traces.append(
                create_trace(
                    lang,
                    stage,
                    wds.by_lang_stage[(lang, stage)],
                )
            )
        traces.append(
            create_trace(
                lang,
                ALL,
                wds.by_lang[lang],
            )
        )

    for stage in stages:
        traces.append(
            create_trace(
                ALL,
                stage,
                wds.by_stage[stage],
            )
        )

    traces.append(
        create_trace(
            ALL,
            ALL,
            wds.all_words,
        )
    )

    for trace in sorted(traces, key=lambda t: t.name):  # pyright: ignore
        fig.add_trace(trace)  # pyright: ignore

    configure_figure(fig)
    return fig
