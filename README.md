# Polyglotka

Visualize [Language Reactor](https://languagereactor.com) data through interactive plots and kanji tables to track your language acquisition progress.

## Name

_Polyglotka_ is a [Slovak word](https://www.google.com/search?q=%22polyglotka%22+site%3A*.sk&sca_esv=3f080a3bfc790179&sxsrf=AE3TifO5N36YjT4dexxsM563QJlsOxL_IA%3A1758898552313&ei=eKnWaNfgEuWuwPAPqdOBmQg&ved=0ahUKEwjX_J_b1_aPAxVlFxAIHalpIIMQ4dUDCBA&uact=5&oq=%22polyglotka%22+site%3A*.sk&gs_lp=Egxnd3Mtd2l6LXNlcnAiFiJwb2x5Z2xvdGthIiBzaXRlOiouc2tIv3xQwQZYrXZwBHgAkAEAmAHwAaAB8AqqAQUwLjUuM7gBA8gBAPgBAfgBApgCAKACAJgDAIgGAZIHAKAH6AKyBwC4BwDCBwDIBwA&sclient=gws-wiz-serp)
that means _female polyglot_.
For example, [Lýdia Machová](https://www.wikiwand.com/sk/articles/L%C3%BDdia_Machov%C3%A1)
is a famous polyglotka.

## Install

Use [pipx](https://pypa.github.io/pipx):

    pipx install ...

## Export Language Reactor Data

On the Language Reactor website open your [saved items](https://www.languagereactor.com/saved-items),
click _Export_, _JSON_, All-All-Any-Any, and _Export_ again.

<img src='media/export_json_window.png' width='400'>

## Configure

Set environment variables with the prefix `POLYGLOTKA_` or just pass flags (they take priority).

    # The title's gonna be "Flag title"
    POLYGLOTKA_PLOTS_TITLE='Env title' polyglotka plots --plots-title 'Flag title'

### Variables

| Name                       | Type      | Default                 | Description                          |
| -------------------------- | --------- | ----------------------- | ------------------------------------ |
| LR_DATA_DIR                | str       | $HOME/Downloads         | Path to the dir w/ your LR exports   |
| LR_DATA_FILES_GLOB_PATTERN | str       | lln_json_items\_\*.json | Glob your json exports               |
| PLOTS_TITLE                | str       | Polyglotka Plots        | The title of the plots               |
| PLOTS_BACKGROUND_COLOR     | str       | \#171717                | Pretty dark by default               |
| PLOTS_SMOOTH               | bool      | True                    | Less accurate but less ugly          |
| ANKI_MIN_COUNTS            | (int,int) | (0,0)                   | Min number of (known,learning) words |
| ANKI_FILTERS               | str       | deck:漢字 is:suspended  | Anki search query stuff              |
| ANKI_KANJI_FIELD           | str       | kanji                   | Anki search query stuff              |

## Run

### `polyglotka plots`

Interactive plots will open in your browser.

Zoom in, zoom out, click on the legend to show/hide graphs, download a picture, have fun.

<img src='media/plots.png' width='400'>

### `polyglotka kanji`

Better pipe the output into [this function](https://github.com/constkolesnyak/dotfiles/blob/3b225ee11388b1c6074caee54ba37e9bb5dc87d2/zsh/.functions.zsh#L1)
to open VS Code with [Rainbow CSV](https://marketplace.visualstudio.com/items?itemName=mechatroner.rainbow-csv):

    polyglotka kanji | codetemp tsv

You will see kanji sorted by frequency.

<img src='media/kanji.png' width='400'>

### `polyglotka anki`

Get the search query for the most frequent kanji. `ANKI_MIN_COUNTS` will cut off the less frequent ones.

If you want to get kanji that are used in at least 7 _known_ words and 9 _learning_ words, run this:

    polyglotka anki --anki-min-counts 7,9

Output:

    deck:漢字 is:suspended (kanji:大 OR kanji:日 OR kanji:話 OR kanji:生 OR kanji:本)

Pipe it directly into the clipboard if you are in a hurry:

    polyglotka anki --anki-min-counts 7,9 | pbcopy

Then paste the search query into Anki.
