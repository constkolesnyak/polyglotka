import colorsys
import os
import threading
import time
import webbrowser
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Iterable, NoReturn
from urllib.parse import urlparse

import dash
import plotly.graph_objects as go
import waitress
from funcy import pluck_attr
from pydantic import BaseModel

from polyglotka.junk.read_lr_data import LearningStage
from polyglotka.junk.read_lr_words import LRWord, read_lr_words

# Configuration Constants #tdc
BACKGROUND_COLOR = '#171717'
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8050
BROWSER_DELAY = 0.3
SHUTDOWN_DELAY = 3.0
CHART_HEIGHT = 800
TAB_TITLE = 'Polyglotka Learning Analytics'

ALL = 'ALL'  # all langs or all learning stages


class PlotConfig(BaseModel):  # tdc
    line_width: int = 3
    marker_size: int = 4
    combined_line_width: int = 4
    combined_marker_size: int = 6
    title_font_size: int = 28
    axis_font_size: int = 16
    tick_font_size: int = 12
    legend_font_size: int = 14


plot_config = PlotConfig()  # tdc


def hsl_to_rgb(h: int, s: int, l: int) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return f'rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})'


def language_code_to_hue(lang_code: str) -> int:
    hash_value = 0
    for i, char in enumerate(lang_code.lower()):
        hash_value += (ord(char) - ord('a') + 1) * (i + 1) * 37
    GOLDEN_RATIO = 0.618033988749
    hue = (hash_value * GOLDEN_RATIO * 360) % 360

    return int(hue)


def get_color(lang: str, stage: str) -> str:
    base_hue = language_code_to_hue(lang)

    match (lang, stage):
        case ('ALL', 'ALL'):
            return 'rgb(255, 255, 255)'
        case ('ALL', LearningStage.LEARNING):
            return 'rgb(108, 92, 231)'
        case ('ALL', LearningStage.KNOWN):
            return 'rgb(162, 155, 254)'
        case (_, 'ALL'):
            return hsl_to_rgb(base_hue, 35, 60)
        case (_, LearningStage.LEARNING):
            return hsl_to_rgb((base_hue - 30) % 360, 90, 50)
        case (_, LearningStage.KNOWN):
            return hsl_to_rgb((base_hue + 45) % 360, 45, 75)
        case _:
            raise ValueError('Bad stage')


class WordDicts:
    def __init__(self, words: list[LRWord]) -> None:
        self.all_words = words
        self.by_lang: defaultdict[str, list[LRWord]] = defaultdict(list)
        self.by_stage: defaultdict[LearningStage, list[LRWord]] = defaultdict(list)
        self.by_lang_stage: defaultdict[
            tuple[str, LearningStage],
            list[LRWord],
        ] = defaultdict(list)

        for word in self.all_words:
            self.by_lang[word.language].append(word)
            self.by_stage[word.learning_stage].append(word)
            self.by_lang_stage[(word.language, word.learning_stage)].append(word)


def smooth_xy_data(words: list[LRWord]) -> tuple[list[datetime], list[int]]:
    word_dates: list[datetime] = sorted(pluck_attr('date', words))
    start, end = word_dates[0].replace(minute=0, second=0, microsecond=0), word_dates[-1]
    hourly_points = [
        start + timedelta(hours=i)
        for i in range(int((end - start).total_seconds() // 3600) + 1)
    ]
    all_x: list[datetime] = sorted(set(word_dates + hourly_points))
    y_data: list[int] = [sum(1 for wd in word_dates if wd <= x) for x in all_x]
    return all_x, y_data


def create_trace(
    language: str,
    learning_stage: str,
    words: list[LRWord],
    line_params: dict[Any, Any],
    marker_params: dict[Any, Any],
) -> go.Scatter:
    x_data, y_data = smooth_xy_data(words)
    name = f'{language.upper()} - {learning_stage.capitalize()}'

    return go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines+markers',
        name=name,
        line=dict(color=get_color(language, learning_stage), **line_params),
        marker=marker_params,
        visible='legendonly' if ALL in name.upper() else True,
    )


def create_learning_analytics_figure() -> go.Figure:
    wds = WordDicts(list(read_lr_words()))  # tdc pass
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
                    {'width': plot_config.line_width},
                    {'size': plot_config.marker_size},
                )
            )
        traces.append(
            create_trace(
                lang,
                ALL,
                wds.by_lang[lang],
                {'width': plot_config.combined_line_width, 'dash': 'dot'},
                {'size': plot_config.combined_marker_size, 'symbol': 'square'},
            )
        )

    for stage in stages:
        traces.append(
            create_trace(
                ALL,
                stage,
                wds.by_stage[stage],
                {'width': plot_config.combined_line_width, 'dash': 'dash'},
                {'size': plot_config.combined_marker_size, 'symbol': 'diamond'},
            )
        )

    traces.append(
        create_trace(
            ALL,
            ALL,
            wds.all_words,
            {'width': plot_config.combined_line_width + 1, 'dash': 'solid'},
            {'size': plot_config.combined_marker_size + 1, 'symbol': 'circle'},
        )
    )

    for trace in sorted(traces, key=lambda t: t.name):  # pyright: ignore
        fig.add_trace(trace)  # pyright: ignore

    _configure_figure_layout(fig)
    return fig


def _configure_figure_layout(fig: go.Figure) -> None:
    fig.update_layout(  # pyright: ignore
        title=dict(
            text='Language Learning Progress Analytics - Interactive Dashboard',
            font=dict(size=plot_config.title_font_size, color='white'),
            x=0.5,
        ),
        xaxis=dict(
            title=dict(
                text='Date', font=dict(size=plot_config.axis_font_size, color='white')
            ),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            tickfont=dict(size=plot_config.tick_font_size, color='white'),
        ),
        yaxis=dict(
            title=dict(
                text='Cumulative Word Count',
                font=dict(size=plot_config.axis_font_size, color='white'),
            ),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            tickfont=dict(size=plot_config.tick_font_size, color='white'),
        ),
        template='plotly_dark',
        plot_bgcolor=BACKGROUND_COLOR,
        paper_bgcolor=BACKGROUND_COLOR,
        font=dict(color='white', size=plot_config.legend_font_size),
        showlegend=True,
        legend=dict(
            font=dict(size=plot_config.legend_font_size, color='white'),
            bgcolor='rgba(0,0,0,0.6)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1,
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top',
        ),
        height=CHART_HEIGHT,
        hovermode='x unified',
        margin=dict(l=60, r=60, t=80, b=60),
    )


def create_dash_app(figure: go.Figure) -> dash.Dash:
    """Needed for margins to match the background color."""
    app = dash.Dash()

    TAB_TITLE = 'Polyglotka Plots'
    app.index_string = f"""
        <!DOCTYPE html>
        <html>
            <head>
                {{%metas%}} <title>{TAB_TITLE}</title> {{%favicon%}} {{%css%}}
            </head>
            <body style="background-color:{BACKGROUND_COLOR};">
                {{%app_entry%}} <footer> {{%config%}} {{%scripts%}} {{%renderer%}} </footer>
            </body>
        </html>
    """

    app.layout = dash.html.Div(
        children=[dash.dcc.Graph(figure=figure, style={'height': '100vh'})],
    )

    return app


def show_plots_and_die() -> None:
    PLOT_URL = 'http://127.0.0.1:8050'

    def _open_browser_and_die() -> NoReturn:
        time.sleep(0.3)
        webbrowser.open(PLOT_URL)
        time.sleep(3)
        os._exit(0)

    dash_app: dash.Dash = create_dash_app(create_learning_analytics_figure())

    threading.Thread(target=_open_browser_and_die, daemon=True).start()
    waitress.serve(
        app=dash_app.server,
        host=urlparse(PLOT_URL).hostname,
        port=urlparse(PLOT_URL).port,
    )


def main() -> None:
    show_plots_and_die()


if __name__ == "__main__":
    main()
