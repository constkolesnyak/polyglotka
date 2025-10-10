# Polyglotka

Visualize [Language Reactor](https://languagereactor.com) data with interactive plots and kanji tables to track your language acquisition progress.

## Name

_Polyglotka_ is a [Slovak word](https://www.google.com/search?q=%22polyglotka%22+site%3A*.sk)
that means _female polyglot_.
For example, [Lýdia Machová](https://www.wikiwand.com/sk/articles/L%C3%BDdia_Machov%C3%A1)
is a famous polyglotka.

## Install

Use [pipx](https://pipx.pypa.io):

    pipx install git+https://github.com/constkolesnyak/polyglotka

## Export Language Reactor Data

On the Language Reactor website, open your [saved items](https://www.languagereactor.com/saved-items),
click _Export_, choose _JSON_, _All-All-Any-Any_, and click _Export_ again.

<img src='media/export_json_window.png' width='400'>

## Configure

Set environment variables with the `POLYGLOTKA_` prefix or pass flags directly.

    # The title's gonna be "Flag title" (flags take priority over env vars)
    POLYGLOTKA_PLOTS_TITLE='Env title' polyglotka plots --plots-title 'Flag title'

### Variables

| Name                       | Type    | Default                 | Description                            |
| -------------------------- | ------- | ----------------------- | -------------------------------------- |
| LR_DATA_DIR                | str     | $HOME/Downloads         | Directory with LR files                |
| LR_DATA_FILES_GLOB_PATTERN | str     | lln_json_items\_\*.json | Glob for LR files                      |
| LR_DATA_FILES_RM           | str     | True                    | Remove LR files after caching the data |
| PLOTS_TITLE                | str     | Polyglotka Plots        | Title of the plots                     |
| PLOTS_BACKGROUND_COLOR     | str     | \#171717                | Background color (dark by default)     |
| PLOTS_SERVER_URL           | str     | http://127.0.0.1:8050   | URL the plots server binds to          |
| PLOTS_SMOOTH               | bool    | True                    | Smoothing for cleaner visuals          |
| PLOTS_HIDE_AGGR            | bool    | True                    | Hide aggregate plots until toggled     |
| ANKI_MIN_COUNTS            | int,int | 0,0                     | Min counts for (known,learning) words  |
| ANKI_FILTERS               | str     | deck:漢字 is:suspended  | Anki search query filters              |
| ANKI_KANJI_FIELD           | str     | kanji                   | Anki field name containing kanji       |

## Run

### `polyglotka plots`

Interactive plots open in your browser.

Zoom in, zoom out, toggle plots, download a picture, push every button in the corner, have fun.

<img src='media/plots.png' width='700'>

### `polyglotka kanji`

Pipe the TSV output into [this function](https://github.com/constkolesnyak/dotfiles/blob/3b225ee11388b1c6074caee54ba37e9bb5dc87d2/zsh/.functions.zsh#L1)
from my dotfiles to open VS Code with [Rainbow CSV](https://marketplace.visualstudio.com/items?itemName=mechatroner.rainbow-csv):

    polyglotka kanji | codetemp tsv

The table shows kanji ordered by the number of known words, then learning words.

<img src='media/kanji.png' width='700'>

### `polyglotka anki`

Generate the search query for kanji with the highest counts of known and learning words. `ANKI_MIN_COUNTS` trims the less frequent ones.

To get kanji that appear in at least 7 known words and 9 learning words, run:

    polyglotka anki --anki-min-counts 7,9

Output:

    deck:漢字 is:suspended (kanji:大 OR kanji:日 OR kanji:話 OR kanji:生 OR kanji:本)

On macOS, pipe the output directly into the clipboard if you are in a hurry:

    polyglotka anki --anki-min-counts 7,9 | pbcopy

Then paste the search query into Anki.

## P.S.

Go [support](https://www.languagereactor.com/pro-mode)
LR devs.
