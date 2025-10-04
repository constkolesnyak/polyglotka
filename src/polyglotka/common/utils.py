import pytest
import dash
import plotly.graph_objects as go

from polyglotka.common.config import config


def run_pytest_k(test_func: str) -> None:
    pytest.main(['-k', test_func])


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
