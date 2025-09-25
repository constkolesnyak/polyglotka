import os
import threading
import time
import webbrowser
from typing import NoReturn
from urllib.parse import urlparse

import dash
import waitress

from polyglotka.common.config import config
from polyglotka.lr_importer.lr_words import import_lr_words
from polyglotka.plots.appearance import create_dash_app
from polyglotka.plots.figure import create_figure


def show_plots_and_die() -> None:
    def _open_browser_and_die() -> NoReturn:
        time.sleep(0.3)
        webbrowser.open(config.PLOTS_SERVER_URL)
        time.sleep(3)
        os._exit(0)

    words = import_lr_words()

    dash_app: dash.Dash = create_dash_app(create_figure(words))

    threading.Thread(target=_open_browser_and_die, daemon=True).start()
    waitress.serve(
        app=dash_app.server,
        host=urlparse(config.PLOTS_SERVER_URL).hostname,
        port=urlparse(config.PLOTS_SERVER_URL).port,
    )


def main() -> None:
    show_plots_and_die()


if __name__ == "__main__":
    main()
