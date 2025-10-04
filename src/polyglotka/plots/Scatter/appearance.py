import colorsys

import dash
import plotly.graph_objects as go

from polyglotka.common.config import config
from polyglotka.lr_importer.lr_items import LearningStage


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


def configure_figure(fig: go.Figure) -> None:
    fig.update_layout(  # pyright: ignore
        title=dict(
            text=config.PLOTS_TITLE,
            font=dict(size=28, color='white'),
            x=0.5,
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(size=20, color='white'), standoff=10),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            tickfont=dict(size=16, color='white'),
        ),
        yaxis=dict(
            title=dict(text='Word Count', font=dict(size=20, color='white'), standoff=15),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            tickfont=dict(size=16, color='white'),
            ticksuffix='  ',
        ),
        template='plotly_dark',
        plot_bgcolor=config.PLOTS_BACKGROUND_COLOR,
        paper_bgcolor=config.PLOTS_BACKGROUND_COLOR,
        font=dict(color='white', size=25),
        showlegend=True,
        legend=dict(
            font=dict(size=20, color='white'),
            bgcolor='rgba(0,0,0,0.6)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1,
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top',
        ),
        height=800,
        hovermode='x unified',
        margin=dict(l=120, r=60, t=90, b=100),
    )

