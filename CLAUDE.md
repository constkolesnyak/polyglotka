# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Polyglotka is a CLI tool for language learners that imports data from Language Reactor and Migaku browser extensions, generates interactive progress plots, and provides kanji tracking for Japanese learners.

## Development Commands

```bash
# Install dependencies
poetry install

# Run CLI commands
poetry run polyglotka <command> [flags]
# Commands: info, plots, kanji, anki, words, subs, clear-cache, import

# Run all tests
poetry run pytest
```

## Architecture

**Entry Point**: `src/polyglotka/main.py` - Uses python-fire to expose CLI commands. The `entrypoint()` function routes commands via pattern matching.

**Configuration**: `src/polyglotka/common/config.py` - Pydantic-settings singleton (`config`) loads from environment variables with `POLYGLOTKA_` prefix. CLI flags override env vars via `config.override()`.

**Module Structure**:

- `importer/` - Parses Language Reactor JSON and Migaku CSV exports, caches word data
- `plots/` - Dash/Plotly-based interactive analytics dashboard
- `simple_commands/` - Standalone commands (kanji, words, excel_to_srt)
- `common/` - Shared config, console utilities, exceptions

**Data Flow**: Export files from `EXPORTED_FILES_DIR` (default: ~/Downloads) → `importer/` parses and caches → `plots/` or `simple_commands/` consume cached data

## Code Style

- Black formatter with 110-char line length, preserved string quotes
- snake_case for functions/variables, PascalCase for classes, kebab-case for CLI flags
- Type hints encouraged; target Python 3.13

## Commits

Short, lowercase, present-tense summaries (e.g., `adjust plots layout`).
