import colorsys
import os
import threading
import time
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn, Optional
from urllib.parse import urlparse

import dash
import plotly.graph_objects as go
import waitress
from pydantic import BaseModel

from polyglotka.junk.read_lr_words import LRWord, read_lr_words

# Configuration Constants
BACKGROUND_COLOR = '#171717'
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8050
BROWSER_DELAY = 0.3
SHUTDOWN_DELAY = 3.0
CHART_HEIGHT = 800
TAB_TITLE = 'Polyglotka Learning Analytics'


class PlotConfig(BaseModel):
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


def generate_color_palette(languages: list[str]):
    color_palette = {  # tdc class?
        'combined': {
            'LEARNING': 'rgb(108, 92, 231)',  # Purple - energetic learning
            'KNOWN': 'rgb(162, 155, 254)',  # Light Purple - calm knowledge
            'ALL': 'rgb(255, 255, 255)',  # White - all combined
        },
        'language_combined': {},
    }

    for lang in languages:
        base_hue = language_code_to_hue(lang)

        # Learning stage: more saturated, warmer hue
        learning_hue = (base_hue - 15) % 360  # Shift towards red/orange
        learning_color = hsl_to_rgb(learning_hue, 80, 55)  # High sat, medium light

        # Known stage: less saturated, cooler hue
        known_hue = (base_hue + 20) % 360  # Shift towards blue/green
        known_color = hsl_to_rgb(known_hue, 65, 70)  # Lower sat, higher light

        # Combined language trace: neutral, desaturated
        combined_color = hsl_to_rgb(base_hue, 35, 60)  # Low sat for subtlety

        color_palette[lang] = {'LEARNING': learning_color, 'KNOWN': known_color}
        color_palette['language_combined'][lang] = combined_color

    return color_palette


class PlotPoints(BaseModel):
    dates: list[datetime]
    counts: list[int]

    def __bool__(self) -> bool:
        return bool(self.dates and self.counts)


def _organize_words() -> tuple[dict, dict, dict, list[LRWord]]:
    """Load and organize words by different dimensions."""
    words = list(read_lr_words())
    by_lang_stage, by_lang, by_stage = (
        defaultdict(list),
        defaultdict(list),
        defaultdict(list),
    )

    for word in words:
        by_lang_stage[(word.language, word.learning_stage)].append(word)
        by_lang[word.language].append(word)
        by_stage[word.learning_stage].append(word)

    return dict(by_lang_stage), dict(by_lang), dict(by_stage), words


def _create_time_series(words: list[LRWord]) -> PlotPoints:
    """Create cumulative time series from words."""
    if not words:
        return PlotPoints(dates=[], counts=[])

    sorted_words = sorted(words, key=lambda w: w.date)
    return PlotPoints(
        dates=[w.date for w in sorted_words], counts=list(range(1, len(sorted_words) + 1))
    )


def _create_trace(
    name: str, time_series: PlotPoints, color: str, line_props: dict, marker_props: dict
) -> Optional[go.Scatter]:
    """Create a plotly trace with given properties."""
    if not time_series:
        return None

    return go.Scatter(
        x=time_series.dates,
        y=time_series.counts,
        mode='lines+markers',
        name=name,
        line=dict(color=color, **line_props),
        marker=dict(**marker_props),
        visible='legendonly' if 'ALL' in name else True,
    )


def create_learning_analytics_figure() -> go.Figure:
    """Create comprehensive learning analytics figure."""
    by_lang_stage, by_lang, by_stage, all_words = _organize_words()
    fig = go.Figure()

    languages = sorted(by_lang.keys())
    stages = sorted(by_stage.keys())
    colors = generate_color_palette(languages)

    # Collect all traces to sort them later
    traces = []

    # Helper function to add traces if data exists
    def add_trace_if_data(words: list[LRWord], trace_func, *args):
        if words:
            trace = trace_func(_create_time_series(words), *args)
            if trace:
                traces.append(trace)

    # Language-stage traces
    for lang in languages:
        for stage in stages:
            words = by_lang_stage.get((lang, stage), [])
            add_trace_if_data(
                words,
                lambda ts, l, s: _create_trace(
                    f'{l.upper()} - {s}',
                    ts,
                    colors[l][s],
                    {'width': plot_config.line_width},
                    {'size': plot_config.marker_size},
                ),
                lang,
                stage,
            )

    # Combined stage traces
    for stage in stages:
        add_trace_if_data(
            by_stage.get(stage, []),
            lambda ts, s: _create_trace(
                f'ALL - {s}',
                ts,
                colors['combined'][s],
                {'width': plot_config.combined_line_width, 'dash': 'dash'},
                {'size': plot_config.combined_marker_size, 'symbol': 'diamond'},
            ),
            stage,
        )

    # Combined language traces
    for lang in languages:
        add_trace_if_data(
            by_lang.get(lang, []),
            lambda ts, l: _create_trace(
                f'{l.upper()} - ALL',
                ts,
                colors['language_combined'][l],
                {'width': plot_config.combined_line_width, 'dash': 'dot'},
                {'size': plot_config.combined_marker_size, 'symbol': 'square'},
            ),
            lang,
        )

    # ALL - ALL trace (all languages, all stages)
    add_trace_if_data(
        all_words,
        lambda ts: _create_trace(
            'ALL - ALL',
            ts,
            colors['combined']['ALL'],
            {'width': plot_config.combined_line_width + 1, 'dash': 'solid'},
            {'size': plot_config.combined_marker_size + 1, 'symbol': 'circle'},
        ),
    )

    # Sort traces by name and add to figure
    traces.sort(key=lambda t: t.name)
    for trace in traces:
        fig.add_trace(trace)

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
