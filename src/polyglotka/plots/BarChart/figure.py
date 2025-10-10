from typing import Iterable

import plotly.express as px
import pandas as pd

from polyglotka.importer.words import Word
from polyglotka.plots.Scatter.appearance import configure_figure

def create_bars(words: Iterable[Word], stacked = True):
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

    y_value = 'cumsum_words_cnt' if stacked else 'words_cnt'

    fig = px.bar(result, x='date', y=y_value)


    configure_figure(fig)

    return fig
