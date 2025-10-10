import dash
import waitress 
from urllib.parse import urlparse
import time
import webbrowser
import os
import threading

from polyglotka.plots.BarChart.figure import create_bars
from polyglotka.common.utils import create_dash_app
from polyglotka.importer.words import import_words
from polyglotka.common.config import config 


def main(stacked = True):
    def _open_browser_and_die():
        time.sleep(0.3)
        webbrowser.open(config.PLOTS_SERVER_URL)

        time.sleep(2)

        os._exit(0)

    words = import_words()

    fig = create_bars(words, stacked)

    dash_app = create_dash_app(fig)

    threading.Thread(target=_open_browser_and_die, daemon=True).start()
    waitress.serve(
        app=dash_app.server,
        host=urlparse(config.PLOTS_SERVER_URL).hostname,
        port=urlparse(config.PLOTS_SERVER_URL).port,
    )
