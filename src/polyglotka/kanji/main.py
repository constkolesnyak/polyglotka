from collections import defaultdict
from itertools import takewhile
from typing import Any, Iterable

import regex as re
from pydantic import BaseModel

from polyglotka.common.config import config
from polyglotka.common.exceptions import UserError
from polyglotka.lr_importer.lr_items import LearningStage
from polyglotka.lr_importer.lr_words import LRWord, import_lr_words


class Kanji(BaseModel):
    kanji: str = ''
    known_words: set[str] = set()
    learning_words: set[str] = set()


def findall_kanji(text: str) -> set[str]:
    return set(re.findall(r"\p{Han}", text, flags=re.VERSION1))


def collect_kanji_with_words(words: Iterable[LRWord]) -> list[Kanji]:
    kanji_dict: defaultdict[str, Kanji] = defaultdict(Kanji)

    for word in words:
        for kanji in findall_kanji(word.word):
            kanji_dict[kanji].kanji = kanji
            match word.learning_stage:
                case LearningStage.KNOWN:
                    kanji_dict[kanji].known_words.add(word.word)
                case LearningStage.LEARNING:
                    kanji_dict[kanji].learning_words.add(word.word)
                case _:
                    raise ValueError('Bad stage')

    return list(kanji_dict.values())


def sorted_desc_kanji(kanji_iterable: Iterable[Kanji]) -> list[Kanji]:
    return sorted(kanji_iterable, key=lambda k: (-len(k.known_words), -len(k.learning_words), k.kanji))


def print_tsv_row(*data: Any):
    print('\t'.join(map(str, data)))


def print_tsv_kanji(kanji_iterable: Iterable[Kanji]) -> None:
    print_tsv_row('Kanji', 'Known Words Count', 'Learning Words Count', 'Known Words', 'Learning Words')

    for kanji in sorted_desc_kanji(kanji_iterable):
        print_tsv_row(
            kanji.kanji,
            len(kanji.known_words),
            len(kanji.learning_words),
            '、'.join(kanji.known_words),
            '、'.join(kanji.learning_words),
        )


def check_min_counts(min_counts: tuple[int, int] | None) -> None:
    if min_counts is None:
        return

    try:
        assert isinstance(min_counts, tuple)
        assert len(min_counts) == 2
        for mc in min_counts:
            assert isinstance(mc, int)
    except AssertionError:
        raise UserError('Expected two integers separated by a comma. E.g. --anki 0,3')


def create_anki_search_query(kanji_iterable: Iterable[Kanji], min_counts: tuple[int, int]):
    top_kanji = takewhile(
        lambda k: (len(k.known_words), len(k.learning_words), k.kanji) >= min_counts,
        sorted_desc_kanji(kanji_iterable),
    )
    return config.ANKI_FILTERS + ' (' + ' OR '.join(f"{config.ANKI_FIELD}:{k.kanji}" for k in top_kanji) + ')'


def main():
    check_min_counts(config.ANKI)
    kanji: list[Kanji] = collect_kanji_with_words(import_lr_words())

    match config.ANKI:
        case None:
            print_tsv_kanji(kanji)
        case _:
            print(create_anki_search_query(kanji, config.ANKI))
