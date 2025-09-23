import os
import threading
import time
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, NoReturn, Optional, Tuple
from urllib.parse import urlparse

import dash
import plotly.graph_objects as go
import waitress

from polyglotka.junk.read_lr_words import LRWord, read_lr_words

# Configuration Constants
BACKGROUND_COLOR = '#171717'
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8050
BROWSER_DELAY = 0.3
SHUTDOWN_DELAY = 3.0
CHART_HEIGHT = 800
TAB_TITLE = 'Polyglotka Learning Analytics'

# Color scheme for different languages and stages
COLOR_PALETTE = {
    'ja': {'LEARNING': 'rgb(255, 107, 107)', 'KNOWN': 'rgb(78, 205, 196)'},  # Red  # Teal
    'de': {'LEARNING': 'rgb(69, 183, 209)', 'KNOWN': 'rgb(249, 202, 36)'},  # Blue  # Yellow
    'combined': {
        'LEARNING': 'rgb(108, 92, 231)',  # Purple
        'KNOWN': 'rgb(162, 155, 254)',  # Light Purple
    },
    'language_combined': {
        'de': 'rgb(150, 150, 150)',  # Gray
        'ja': 'rgb(200, 200, 200)',  # Light Gray
    },
}


class Language(Enum):
    """Supported languages for learning analytics."""

    GERMAN = 'de'
    JAPANESE = 'ja'


class LearningStage(Enum):
    """Learning stages for vocabulary acquisition."""

    LEARNING = 'LEARNING'
    KNOWN = 'KNOWN'


@dataclass
class PlotConfig:
    """Configuration for plot appearance and behavior."""

    line_width: int = 3
    marker_size: int = 4
    combined_line_width: int = 4
    combined_marker_size: int = 6
    title_font_size: int = 28
    axis_font_size: int = 16
    tick_font_size: int = 12
    legend_font_size: int = 14


@dataclass
class TimeSeriesData:
    """Container for time series data points."""

    dates: List[datetime]
    counts: List[int]

    def is_empty(self) -> bool:
        """Check if the time series data is empty."""
        return len(self.dates) == 0 or len(self.counts) == 0


@dataclass
class WordDatasets:
    """Organized word datasets for analytics."""

    all_words: List[LRWord]
    by_language_and_stage: Dict[Tuple[str, str], List[LRWord]]
    by_language: Dict[str, List[LRWord]]
    by_stage: Dict[str, List[LRWord]]


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


def create_cumulative_time_series(words: List[LRWord]) -> TimeSeriesData:
    """Create cumulative time series data from a list of words.

    Args:
        words: List of LRWord objects to process

    Returns:
        TimeSeriesData: Dates and cumulative counts for plotting
    """
    if not words:
        return TimeSeriesData(dates=[], counts=[])

    # Sort words by date to ensure proper cumulative counting
    sorted_words = sorted(words, key=lambda w: w.date)

    dates = [word.date for word in sorted_words]
    counts = list(range(1, len(sorted_words) + 1))

    return TimeSeriesData(dates=dates, counts=counts)


def create_language_stage_trace(
    language: str, stage: str, time_series: TimeSeriesData, config: PlotConfig
) -> Optional[go.Scatter]:
    """Create a trace for a specific language-stage combination.

    Args:
        language: Language code (e.g., 'de', 'ja')
        stage: Learning stage ('LEARNING' or 'KNOWN')
        time_series: Time series data for the trace
        config: Plot configuration settings

    Returns:
        Plotly Scatter trace or None if data is empty
    """
    if time_series.is_empty():
        return None

    color = COLOR_PALETTE[language][stage]
    return go.Scatter(
        x=time_series.dates,
        y=time_series.counts,
        mode='lines+markers',
        name=f'{language.upper()} - {stage}',
        line=dict(color=color, width=config.line_width),
        marker=dict(size=config.marker_size),
        visible=True,
    )


def create_combined_stage_trace(
    stage: str, time_series: TimeSeriesData, config: PlotConfig
) -> Optional[go.Scatter]:
    """Create a trace for combined languages by stage.

    Args:
        stage: Learning stage ('LEARNING' or 'KNOWN')
        time_series: Time series data for the trace
        config: Plot configuration settings

    Returns:
        Plotly Scatter trace or None if data is empty
    """
    if time_series.is_empty():
        return None

    color = COLOR_PALETTE['combined'][stage]
    return go.Scatter(
        x=time_series.dates,
        y=time_series.counts,
        mode='lines+markers',
        name=f'ALL LANGUAGES - {stage}',
        line=dict(color=color, width=config.combined_line_width, dash='dash'),
        marker=dict(size=config.combined_marker_size, symbol='diamond'),
        visible=True,
    )


def create_combined_language_trace(
    language: str, time_series: TimeSeriesData, config: PlotConfig
) -> Optional[go.Scatter]:
    """Create a trace for all stages of a specific language.

    Args:
        language: Language code (e.g., 'de', 'ja')
        time_series: Time series data for the trace
        config: Plot configuration settings

    Returns:
        Plotly Scatter trace or None if data is empty
    """
    if time_series.is_empty():
        return None

    color = COLOR_PALETTE['language_combined'][language]
    return go.Scatter(
        x=time_series.dates,
        y=time_series.counts,
        mode='lines+markers',
        name=f'{language.upper()} - ALL STAGES',
        line=dict(color=color, width=config.combined_line_width, dash='dot'),
        marker=dict(size=config.combined_marker_size, symbol='square'),
        visible=True,
    )


def create_learning_analytics_figure() -> go.Figure:
    """Create comprehensive learning analytics with all plots on the same axes.

    Returns:
        Interactive Plotly figure with learning progress visualization
    """
    datasets = load_and_organize_words()
    config = PlotConfig()
    fig = go.Figure()

    # Language-stage combination traces
    language_stage_combinations = [
        (Language.GERMAN.value, LearningStage.LEARNING.value),
        (Language.GERMAN.value, LearningStage.KNOWN.value),
        (Language.JAPANESE.value, LearningStage.LEARNING.value),
        (Language.JAPANESE.value, LearningStage.KNOWN.value),
    ]

    for language, stage in language_stage_combinations:
        words = datasets.by_language_and_stage.get((language, stage), [])
        time_series = create_cumulative_time_series(words)
        trace = create_language_stage_trace(language, stage, time_series, config)
        if trace:
            fig.add_trace(trace)

    # Combined stage traces (all languages)
    for stage in [LearningStage.LEARNING.value, LearningStage.KNOWN.value]:
        words = datasets.by_stage.get(stage, [])
        time_series = create_cumulative_time_series(words)
        trace = create_combined_stage_trace(stage, time_series, config)
        if trace:
            fig.add_trace(trace)

    # Combined language traces (all stages)
    for language in [Language.GERMAN.value, Language.JAPANESE.value]:
        words = datasets.by_language.get(language, [])
        time_series = create_cumulative_time_series(words)
        trace = create_combined_language_trace(language, time_series, config)
        if trace:
            fig.add_trace(trace)

    # Apply layout configuration
    _configure_figure_layout(fig, config)
    return fig


def _configure_figure_layout(fig: go.Figure, config: PlotConfig) -> None:
    """Configure the layout and styling of the figure.

    Args:
        fig: Plotly figure to configure
        config: Plot configuration settings
    """
    fig.update_layout(
        title=dict(
            text='Language Learning Progress Analytics - Interactive Dashboard',
            font=dict(size=config.title_font_size, color='white'),
            x=0.5,
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(size=config.axis_font_size, color='white')),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            tickfont=dict(size=config.tick_font_size, color='white'),
        ),
        yaxis=dict(
            title=dict(
                text='Cumulative Word Count',
                font=dict(size=config.axis_font_size, color='white'),
            ),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            tickfont=dict(size=config.tick_font_size, color='white'),
        ),
        template='plotly_dark',
        plot_bgcolor=BACKGROUND_COLOR,
        paper_bgcolor=BACKGROUND_COLOR,
        font=dict(color='white', size=config.legend_font_size),
        showlegend=True,
        legend=dict(
            font=dict(size=config.legend_font_size, color='white'),
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
