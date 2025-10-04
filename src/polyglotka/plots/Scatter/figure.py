from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go  # pyright: ignore
from funcy import pluck_attr  # pyright: ignore

from polyglotka.common.config import config
from polyglotka.lr_importer.lr_items import LearningStage
from polyglotka.lr_importer.lr_words import LRWord
from polyglotka.plots.Scatter.appearance import configure_figure, get_color
from polyglotka.lr_importer.lr_words import WordDicts

ALL = 'ALL'  # all langs or all learning stages


def create_points(words: Iterable[LRWord]) -> tuple[list[datetime], list[int]]:
    word_dates: list[datetime] = sorted(pluck_attr('date', words))
    start, end = word_dates[0].replace(minute=0, second=0, microsecond=0), word_dates[-1]
    hourly_points = [
        start + timedelta(hours=i) for i in range(int((end - start).total_seconds() // 3600) + 1)
    ]
    x_data: list[datetime] = sorted(set(word_dates + hourly_points))
    y_data: list[int] = [sum(1 for wd in word_dates if wd <= x) for x in x_data]

    if config.PLOTS_SMOOTH:
        series = pd.Series(y_data, index=pd.to_datetime(x_data)).sort_index()
        rate = series.diff().fillna(0).resample('h').sum()  # type: ignore
        y_smooth = rate.ewm(halflife=6, adjust=False).mean().cumsum()
        y_smooth *= series.iloc[-1] / y_smooth.iloc[-1]
        x_data, y_data = y_smooth.index, y_smooth.values.round().astype(int).tolist()

    return x_data, y_data


def create_trace(
    language: str,
    learning_stage: str,
    words: Iterable[LRWord],
) -> go.Scatter:
    x_data, y_data = create_points(words)
    name = f'{language.upper()} - {learning_stage.capitalize()}'

    line_width = 3
    visible = True
    if ALL in name.upper():
        line_width = 4
        if config.PLOTS_HIDE_AGGR:
            visible = 'legendonly'

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


def create_figure(words: Iterable[LRWord]) -> go.Figure:
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
