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


@dataclass
class WordDatasets:
    """Organized word datasets for analytics."""

    all_words: list[LRWord]
    by_language_and_stage: dict[tuple[str, str], list[LRWord]]
    by_language: dict[str, list[LRWord]]
    by_stage: dict[str, list[LRWord]]


def load_and_organize_words() -> WordDatasets:
    """Load words from data source and organize them by different dimensions.

    Returns:
        WordDatasets: Organized word data for analytics
    """
    words = list(read_lr_words())

    # Initialize collections
    by_lang_stage = defaultdict(list)
    by_lang = defaultdict(list)
    by_stage = defaultdict(list)

    # Organize words by different dimensions
    for word in words:
        key = (word.language, word.learning_stage)
        by_lang_stage[key].append(word)
        by_lang[word.language].append(word)
        by_stage[word.learning_stage].append(word)

    return WordDatasets(
        all_words=words,
        by_language_and_stage=dict(by_lang_stage),
        by_language=dict(by_lang),
        by_stage=dict(by_stage),
    )


def create_cumulative_time_series(words: list[LRWord]) -> PlotPoints:
    """Create cumulative time series data from a list of words.

    Args:
        words: list of LRWord objects to process

    Returns:
        TimeSeriesData: Dates and cumulative counts for plotting
    """
    if not words:
        return PlotPoints(dates=[], counts=[])

    # Sort words by date to ensure proper cumulative counting
    sorted_words = sorted(words, key=lambda w: w.date)

    dates = [word.date for word in sorted_words]
    counts = list(range(1, len(sorted_words) + 1))

    return PlotPoints(dates=dates, counts=counts)


def create_language_stage_trace(
    language: str,
    stage: str,
    time_series: PlotPoints,
    color_palette: dict,
) -> Optional[go.Scatter]:
    """Create a trace for a specific language-stage combination.

    Args:
        language: Language code (e.g., 'de', 'ja', 'fr', etc.)
        stage: Learning stage ('LEARNING' or 'KNOWN')
        time_series: Time series data for the trace
        config: Plot configuration settings
        color_palette: Dynamic color palette for languages

    Returns:
        Plotly Scatter trace or None if data is empty
    """
    if not time_series:
        return None

    color = color_palette[language][stage]
    return go.Scatter(
        x=time_series.dates,
        y=time_series.counts,
        mode='lines+markers',
        name=f'{language.upper()} - {stage}',
        line=dict(color=color, width=plot_config.line_width),
        marker=dict(size=plot_config.marker_size),
        visible=True,
    )


def create_combined_stage_trace(
    stage: str, time_series: PlotPoints, color_palette: dict
) -> Optional[go.Scatter]:
    """Create a trace for combined languages by stage.

    Args:
        stage: Learning stage ('LEARNING' or 'KNOWN')
        time_series: Time series data for the trace
        config: Plot configuration settings
        color_palette: Dynamic color palette for languages

    Returns:
        Plotly Scatter trace or None if data is empty
    """
    if not time_series:
        return None

    color = color_palette['combined'][stage]
    return go.Scatter(
        x=time_series.dates,
        y=time_series.counts,
        mode='lines+markers',
        name=f'ALL LANGUAGES - {stage}',
        line=dict(color=color, width=plot_config.combined_line_width, dash='dash'),
        marker=dict(size=plot_config.combined_marker_size, symbol='diamond'),
        visible=True,
    )


def create_combined_language_trace(
    language: str, time_series: PlotPoints, color_palette: dict
) -> Optional[go.Scatter]:
    """Create a trace for all stages of a specific language.

    Args:
        language: Language code (e.g., 'de', 'ja', 'fr', etc.)
        time_series: Time series data for the trace
        config: Plot configuration settings
        color_palette: Dynamic color palette for languages

    Returns:
        Plotly Scatter trace or None if data is empty
    """
    if not time_series:
        return None

    color = color_palette['language_combined'][language]
    return go.Scatter(
        x=time_series.dates,
        y=time_series.counts,
        mode='lines+markers',
        name=f'{language.upper()} - ALL STAGES',
        line=dict(color=color, width=plot_config.combined_line_width, dash='dot'),
        marker=dict(size=plot_config.combined_marker_size, symbol='square'),
        visible=True,
    )


def create_learning_analytics_figure() -> go.Figure:
    """Create comprehensive learning analytics with all plots on the same axes.

    Returns:
        Interactive Plotly figure with learning progress visualization
    """
    datasets = load_and_organize_words()
    fig = go.Figure()

    # Get all languages and stages dynamically from the data
    all_languages = sorted(datasets.by_language.keys())
    all_stages = sorted(datasets.by_stage.keys())

    # Generate dynamic color palette based on available languages
    color_palette = generate_color_palette(all_languages)

    # Language-stage combination traces (dynamic based on available data)
    for language in all_languages:
        for stage in all_stages:
            words = datasets.by_language_and_stage.get((language, stage), [])
            if words:  # Only create traces for combinations that have data
                time_series = create_cumulative_time_series(words)
                trace = create_language_stage_trace(
                    language, stage, time_series, color_palette
                )
                if trace:
                    fig.add_trace(trace)

    # Combined stage traces (all languages)
    for stage in all_stages:
        words = datasets.by_stage.get(stage, [])
        if words:  # Only create traces for stages that have data
            time_series = create_cumulative_time_series(words)
            trace = create_combined_stage_trace(stage, time_series, color_palette)
            if trace:
                fig.add_trace(trace)

    # Combined language traces (all stages)
    for language in all_languages:
        words = datasets.by_language.get(language, [])
        if words:  # Only create traces for languages that have data
            time_series = create_cumulative_time_series(words)
            trace = create_combined_language_trace(language, time_series, color_palette)
            if trace:
                fig.add_trace(trace)

    # Apply layout configuration
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
