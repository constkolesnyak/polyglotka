from collections import defaultdict
from typing import Any, Iterable

import regex as re
from pydantic import BaseModel

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


def print_tsv_row(*data: Any):
    print('\t'.join(map(str, data)))


def print_tsv_kanji(kanji_list: list[Kanji]) -> None:
    print_tsv_row('Kanji', 'Known Words Count', 'Learning Words Count', 'Known Words', 'Learning Words')

    sorted_kanji = sorted(kanji_list, key=lambda k: (-len(k.known_words), -len(k.learning_words)))
    for kanji in sorted_kanji:
        print_tsv_row(
            kanji.kanji,
            len(kanji.known_words),
            len(kanji.learning_words),
            '、'.join(kanji.known_words),
            '、'.join(kanji.learning_words),
        )


def main():
    print_tsv_kanji(collect_kanji_with_words(import_lr_words()))
