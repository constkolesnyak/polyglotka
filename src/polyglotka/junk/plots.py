import math
import os
import threading
import time
import webbrowser
from typing import NoReturn
from urllib.parse import urlparse

import dash
import plotly.graph_objects as go
import waitress

BACKGROUND_COLOR = '#171717'


def create_trig_data() -> dict[str, list[float]]:
    x = [i * 0.1 for i in range(100)]
    return {
        'x': x,
        'sin_x': [math.sin(val) for val in x],
        'cos_x': [math.cos(val) for val in x],
        'sin_2x': [math.sin(2 * val) for val in x],
        'cos_2x': [math.cos(2 * val) for val in x],
    }


def create_figure() -> go.Figure:
    data = create_trig_data()

    fig = go.Figure()
    traces = [
        ('sin(x)', data['sin_x'], 'red'),
        ('cos(x)', data['cos_x'], 'blue'),
        ('sin(2x)', data['sin_2x'], 'green'),
        ('cos(2x)', data['cos_2x'], 'orange'),
    ]

    for name, y_data, color in traces:
        fig.add_trace(  # pyright: ignore
            go.Scatter(
                x=data['x'], y=y_data, mode='lines', name=name, line=dict(color=color)
            )
        )

    fig.update_layout(  # pyright: ignore
        title='Interactive Trigonometric Functions',
        xaxis_title='X Values',
        yaxis_title='Y Values',
        template='plotly_dark',
        plot_bgcolor=BACKGROUND_COLOR,
        paper_bgcolor=BACKGROUND_COLOR,
        legend=dict(font=dict(size=20)),
    )
    fig.update_yaxes(ticksuffix='  ')  # pyright: ignore

    return fig


def create_dash_app() -> dash.Dash:
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
        children=[dash.dcc.Graph(figure=create_figure(), style={'height': '100vh'})],
    )

    return app


def show_plots_and_die() -> None:
    PLOT_URL = 'http://127.0.0.1:8050'

    def _open_browser_and_die() -> NoReturn:
        time.sleep(0.3)
        webbrowser.open(PLOT_URL)
        time.sleep(3)
        os._exit(0)

    threading.Thread(target=_open_browser_and_die, daemon=True).start()
    waitress.serve(
        app=create_dash_app().server,
        host=urlparse(PLOT_URL).hostname,
        port=urlparse(PLOT_URL).port,
    )


def main() -> None:
    show_plots_and_die()


if __name__ == "__main__":
    main()
