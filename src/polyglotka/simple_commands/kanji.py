from collections import defaultdict
from itertools import takewhile
from typing import Any, Callable, Iterable

import regex as re
from pydantic import BaseModel

from polyglotka.common.config import config
from polyglotka.importer.words import LearningStage, Word, import_words


class Kanji(BaseModel):
    char: str = ''
    known_words: set[str] = set()
    learning_words: set[str] = set()


def find_kanji_chars(text: str) -> set[str]:
    return set(re.findall(r'\p{Han}', text, flags=re.VERSION1))


def collect_kanji_with_words(words: Iterable[Word]) -> list[Kanji]:
    kanji_dict: defaultdict[str, Kanji] = defaultdict(Kanji)

    for word in words:
        if word.language == 'ja':
            for char in find_kanji_chars(word.word):
                kanji_dict[char].char = char
                match word.learning_stage:
                    case LearningStage.KNOWN:
                        kanji_dict[char].known_words.add(word.word)
                    case LearningStage.LEARNING:
                        kanji_dict[char].learning_words.add(word.word)
                    case _:
                        raise ValueError('Bad stage')

    return list(kanji_dict.values())


def sorted_desc_kanji(kanji_iterable: Iterable[Kanji]) -> list[Kanji]:
    return sorted(kanji_iterable, key=lambda k: (-len(k.known_words), -len(k.learning_words), k.char))


def create_tsv_row(*data: Any) -> str:
    return '\t'.join(map(str, data))


def create_tsv_kanji(kanji_sorted_desc: Iterable[Kanji]) -> str:
    tsv_kanji: list[str] = [
        create_tsv_row('Kanji', 'Known Words Count', 'Learning Words Count', 'Known Words', 'Learning Words')
    ]

    for kanji in kanji_sorted_desc:
        tsv_kanji.append(
            create_tsv_row(
                kanji.char,
                len(kanji.known_words),
                len(kanji.learning_words),
                '、'.join(kanji.known_words),
                '、'.join(kanji.learning_words),
            )
        )

    return '\n'.join(tsv_kanji)


def create_anki_search_query(kanji_sorted_desc: Iterable[Kanji]) -> str:
    top_kanji = takewhile(
        lambda k: (len(k.known_words), len(k.learning_words)) >= config.anki_min_counts,
        kanji_sorted_desc,
    )
    kanji_or_kanji = ' OR '.join(f'{config.ANKI_KANJI_FIELD}:{k.char}' for k in top_kanji)

    return (
        f'{config.ANKI_FILTERS} ({kanji_or_kanji})'
        if kanji_or_kanji
        else 'Kanji not found. Try lowering ANKI_MIN_COUNTS'
    )


def main(anki: bool = False) -> None:
    func: Callable[..., str] = create_anki_search_query if anki else create_tsv_kanji
    print(func(sorted_desc_kanji(collect_kanji_with_words(import_words()))))
