from typing import Iterable

import plotly.express as px
import pandas as pd

from polyglotka.lr_importer.lr_words import LRWord
from polyglotka.lr_importer.lr_words import import_lr_words
from polyglotka.plots.Scatter.appearance import configure_figure

def create_bars(words: Iterable[LRWord], stacked = True):
    w = [
        {
            'key': w.key,
            'word': w.word,
            'language': w.language,
            'learning_stage': w.learning_stage,
            'date': w.date
        } for w in words
        ]
    
    df = pd.DataFrame(w)

    df['date'] = pd.to_datetime(df['date'])

    df['date'] = df['date'].dt.normalize()

    words_count_per_date = df.groupby('date')['word'].count().reset_index(name='words_cnt')

    result = words_count_per_date.set_index('date').resample('D').sum().fillna(0).reset_index()

    result['cumsum_words_cnt'] = result['words_cnt'].cumsum()

    print(result)

    y_value = 'cumsum_words_cnt' if stacked else 'words_cnt'

    fig = px.bar(result, x='date', y=y_value)


    configure_figure(fig)

    return fig
