# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Setup
```bash
poetry install
```

### Running Commands
- Use `poetry run polyglotka <command>` to run CLI commands within the Poetry virtualenv
- Available commands: `info`, `plots`, `kanji`, `anki`, `words`, `subs`, `clear-cache`
- Preview CLI options: `poetry run polyglotka plots --help`

### Testing
```bash
# Full test suite (verbose output configured in pyproject.toml)
poetry run pytest

# Quick smoke tests only
poetry run pytest -m smoke

# Run specific test file
poetry run pytest tests/test_main.py

# Coverage reporting
poetry run coverage run -m pytest && poetry run coverage report
```

### Code Formatting
```bash
# Format code with Black (110-char line length, preserve string quotes)
poetry run black .
```

## Architecture

### Core Structure
- **Entry Point**: `src/polyglotka/main.py` exposes CLI commands registered in `pyproject.toml`
- **Config System**: Singleton config in `src/polyglotka/common/config.py` using Pydantic with `POLYGLOTKA_` environment variable prefix
- **Command Routing**: Fire-based CLI with enum-driven command dispatch in `main.py`

### Module Organization
- `common/`: Shared utilities (config, console, exceptions, utils)
- `importer/`: Language Reactor and Migaku data import logic (words.py, words_cache.py)
- `plots/`: Interactive Plotly/Dash analytics dashboards
- `simple_commands/`: Individual command implementations (kanji.py, words_exporter.py, excel_to_srt.py)

### Key Patterns
- **Configuration Override**: CLI flags override environment variables via `config.override(config_upd)`
- **Command Pattern**: Each command has dedicated main function imported and called from `main.py`
- **Caching**: Words data cached to `~/.cache/polyglotka/words.json` via `words_cache` module
- **Error Handling**: Custom `UserError` exception for user-facing error messages

### Dependencies
- **CLI**: Fire for command line interface
- **Data**: Pandas/NumPy for data processing, Pydantic for config/validation
- **Visualization**: Plotly + Dash for interactive plots served on localhost:8050
- **File Processing**: Path.py for filesystem operations, openpyxl for Excel files

## Testing

### Test Structure
- Tests mirror `src/` layout in `tests/`
- Sample data in `tests/testing_data/` (migaku_words_*.csv)
- Use pytest fixtures and monkeypatching for isolation
- Smoke test marker (`-m smoke`) for core command validation

### Configuration in pyproject.toml
- Verbose output (`-v`) enabled by default
- Test discovery in `tests/` with `src/` in Python path
- Coverage excludes tests and `__init__.py`, plus `raise NotImplementedError` lines

## Environment Variables

All configuration uses `POLYGLOTKA_` prefix. Key variables:
- `POLYGLOTKA_EXPORTED_FILES_DIR`: Location of Language Reactor/Migaku exports (default: ~/Downloads)
- `POLYGLOTKA_PLOTS_TITLE`: Dashboard title
- `POLYGLOTKA_ANKI_MIN_COUNTS`: Comma-separated min counts for known,learning words
- `POLYGLOTKA_PROCESSED_FILES_RM`: Whether to delete processed files

See `src/polyglotka/common/config.py` for complete list.

## Code Style

- Python 3.13 target with type hints
- Black formatting: 110-char lines, preserved string quotes
- snake_case functions/variables, PascalCase classes, kebab-case CLI flags
- Manual import sorting (no isort)
- Prefer pure functions over script-style code