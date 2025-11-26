import colorsys
from datetime import datetime, timedelta

import dash
import plotly.graph_objects as go  # pyright: ignore

from polyglotka.common.config import config
from polyglotka.importer.words import LearningStage


def hsl_to_rgb(h: int, s: int, l: int) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return f'rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})'


def language_code_to_hue(lang_code: str) -> int:
    # Colors spaced ~36 degrees apart (360/10) for visual distinction
    LANGUAGE_HUES = {
        'ALL': 260,  # Purple
        'KO': 330,  # Pink-red
        'FR': 300,  # Magenta
        'JA': 210,  # Blue
        'DE': 90,  # Yellow-green
        'ES': 30,  # Orange
        'IT': 120,  # Green
        'PT': 150,  # Green-cyan
        'EN': 0,  # Red
        #
        'ZH': 60,  # Yellow
        'RU': 180,  # Cyan
        'AR': 240,  # Blue-purple
        'HI': 45,  # Orange-yellow
        'NL': 165,  # Teal
    }

    lang_upper = lang_code.upper()
    if lang_upper in LANGUAGE_HUES:
        return LANGUAGE_HUES[lang_upper]

    # Fallback: FNV-1a hash for uncommon language codes
    FNV_OFFSET = 2166136261
    FNV_PRIME = 16777619
    hash_value = FNV_OFFSET
    for char in lang_code.lower():
        hash_value ^= ord(char)
        hash_value = (hash_value * FNV_PRIME) & 0xFFFFFFFF

    return hash_value % 360


def get_color(lang: str, stage: str) -> str:
    base_hue = language_code_to_hue(lang)

    match (stage):
        case 'ALL':
            return hsl_to_rgb(base_hue, 35, 60)
        case LearningStage.LEARNING:
            return hsl_to_rgb(base_hue + 20, 30, 65)
        case LearningStage.KNOWN:
            return hsl_to_rgb(base_hue, 95, 55)
        case _:
            raise ValueError('Bad stage')


def configure_figure(fig: go.Figure, traces: list[go.Scatter]) -> None:
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
            title=dict(text=config.PLOTS_Y_TITLE, font=dict(size=20, color='white'), standoff=15),
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

    visible_traces: list[go.Scatter] = [
        t for t in traces if t.visible in (True, 'legendonly')  # pyright: ignore
    ]
    max_y: int = max(  # pyright: ignore
        max(t.y)  # pyright: ignore
        for t in visible_traces
        if t.y and config.NATIVE_LANG not in t.name.lower()  # pyright: ignore
    )
    fig.update_yaxes(range=[config.PLOTS_Y_MIN, max_y * 1.05])  # pyright: ignore

    if config.PLOTS_X_DAYS_DELTA:
        fig.update_xaxes(  # pyright: ignore
            range=[datetime.now() - timedelta(days=config.PLOTS_X_DAYS_DELTA), datetime.now()]
        )


def create_dash_app(figure: go.Figure) -> dash.Dash:
    """Needed for margins to match the background color."""
    app = dash.Dash()

    app.index_string = f"""
        <!DOCTYPE html>
        <html>
            <head>
                {{%metas%}} <title>{config.PLOTS_TITLE}</title> {{%favicon%}} {{%css%}}
            </head>
            <body style="background-color:{config.PLOTS_BACKGROUND_COLOR};">
                {{%app_entry%}} <footer> {{%config%}} {{%scripts%}} {{%renderer%}} </footer>
            </body>
        </html>
    """
    app.layout = dash.html.Div(
        children=[dash.dcc.Graph(figure=figure, style={'height': '100vh'})],
    )

    return app
