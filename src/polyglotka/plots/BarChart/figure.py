from typing import Iterable

import plotly.express as px
import pandas as pd

from polyglotka.lr_importer.lr_words import LRWord
from polyglotka.lr_importer.lr_words import import_lr_words

def create_bars(words: Iterable[LRWord]):
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

    print(result)

    fig = px.bar(result, x='date', y='words_cnt')

    return fig
