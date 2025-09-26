import logging
import os
import threading
import time
import webbrowser
from typing import NoReturn
from urllib.parse import urlparse

import dash
import waitress

from polyglotka.common.config import config
from polyglotka.common.console import Progress, ProgressType
from polyglotka.lr_importer.lr_words import import_lr_words
from polyglotka.plots.appearance import create_dash_app
from polyglotka.plots.figure import create_figure

# Silence the waitress queue depth warnings
logging.getLogger('waitress.queue').setLevel(logging.ERROR)


def main() -> None:
    def _open_browser_and_die(progress: Progress) -> NoReturn:
        time.sleep(0.3)
        webbrowser.open(config.PLOTS_SERVER_URL)

        progress.update('Exiting')
        time.sleep(2)
        progress.__exit__(None, None, None)
        os._exit(0)

    words = import_lr_words()
    with Progress(progress_type=ProgressType.TEXT, text='Plotting') as progress:
        figure = create_figure(words)
        dash_app: dash.Dash = create_dash_app(figure)

        progress.update('Opening browser')
        threading.Thread(target=_open_browser_and_die, kwargs=dict(progress=progress), daemon=True).start()
        waitress.serve(
            app=dash_app.server,
            host=urlparse(config.PLOTS_SERVER_URL).hostname,
            port=urlparse(config.PLOTS_SERVER_URL).port,
        )
