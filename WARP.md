# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Setup and Dependencies
```bash
poetry install
```

### Running the Application
```bash
# Main CLI entry point
poetry run polyglotka <COMMAND>

# Available commands: PLOTS, KANJI, ANKI
poetry run polyglotka PLOTS
poetry run polyglotka KANJI
poetry run polyglotka ANKI

# Development iteration (bypassing entry point)
poetry run python src/polyglotka/main.py PLOTS

# Override configuration via CLI flags
poetry run polyglotka PLOTS --lr-data-dir=/path/to/data
```

### Testing
```bash
# Run all tests
poetry run pytest -v

# Run smoke tests only
poetry run pytest -v -m smoke

# Run specific test files
poetry run pytest tests/test_main.py -v
```

### Code Quality
```bash
# Format code (Black configuration: line-length=110, skip-string-normalization=true)
poetry run black src/ tests/

# Type checking
poetry run mypy src/
```

## Architecture Overview

### CLI Structure
The application uses Python Fire for command-line interface with three main commands:
- **PLOTS**: Launches a Dash web server for interactive data visualization
- **KANJI**: Generates TSV output of kanji analysis from Language Reactor data
- **ANKI**: Creates Anki search queries for kanji study based on learning progress

### Module Organization
```
src/polyglotka/
├── main.py              # CLI entry point and command routing
├── common/              # Shared utilities and configuration
│   ├── config.py        # Pydantic-based configuration with .env support
│   ├── console.py       # Progress indicators and terminal helpers
│   ├── exceptions.py    # Custom exception classes (UserError)
│   └── utils.py         # General utilities
├── lr_importer/         # Language Reactor data processing
│   ├── lr_items.py      # Raw JSON item parsing and Pydantic models
│   └── lr_words.py      # Word extraction and deduplication logic  
├── plots/               # Dash web application for visualization
│   ├── main.py          # Web server setup and browser automation
│   ├── figure.py        # Plotly figure generation
│   └── appearance.py    # Dash app layout and styling
├── kanji/               # Japanese character analysis
│   └── main.py          # Kanji extraction and TSV/Anki output
└── junk/                # Experimental code and development spikes
```

### Data Flow Architecture
1. **Import**: `lr_importer` reads Language Reactor JSON exports and converts to typed Python objects
2. **Transform**: Domain-specific modules (`kanji`, `plots`) process the imported data
3. **Output**: Results are either served via Dash web interface or printed as CLI output

### Configuration System
- Uses `pydantic-settings` for type-safe configuration
- Environment variables prefixed with `POLYGLOTKA_` 
- `.env` file support for local development
- CLI flag overrides for runtime configuration
- Key settings: `LR_DATA_DIR`, `PLOTS_SERVER_URL`, `ANKI_MIN_COUNTS`

### Key Design Patterns
- **Pydantic Models**: Extensive use for data validation and parsing (Language Reactor JSON structure)
- **Command Pattern**: CLI commands routed through `main.entrypoint()` function  
- **Domain Separation**: Clear boundaries between data import, processing, and presentation
- **Progressive Enhancement**: Core functionality works without web interface, Dash adds visualization

### Testing Strategy
- Pytest with fixtures in `tests/conftest.py`
- Tests mirror module structure (`tests/test_main.py`, `tests/test_config.py`)
- Behavioral test naming (`test_loads_language_reactor_items`)
- Smoke tests for quick validation (`-m smoke`)
- Mock filesystem and external dependencies

### Language Reactor Integration
Language Reactor exports Japanese learning data as JSON files. The `lr_importer` module:
- Parses complex nested JSON structures with video/subtitle context
- Extracts word learning stages (KNOWN, LEARNING)
- Handles deduplication based on timestamps
- Supports YouTube, Netflix, and video file sources

## Python and Dependencies

### Python Version
- Target: Python 3.13
- Type annotations required for public functions
- Import organization: stdlib, third-party, local (sorted within groups)

### Key Dependencies
- **pydantic**: Data validation and settings management
- **fire**: Command-line interface generation
- **dash**: Web application framework for plots
- **plotly**: Interactive visualization
- **waitress**: Production WSGI server
- **regex**: Advanced regex with Unicode property support for kanji detection

### Code Style
- Black formatter: `line-length = 110`, `skip-string-normalization = true`
- `snake_case` for functions/modules, `PascalCase` for classes/enums
- `UPPERCASE` for constants and environment variables
- Raise `UserError` for user-facing CLI validation failures

## Environment Configuration

### Required Variables
```bash
# Language Reactor data directory (required for all commands)
POLYGLOTKA_LR_DATA_DIR=/path/to/language-reactor/exports

# Optional overrides
POLYGLOTKA_PLOTS_SERVER_URL=http://127.0.0.1:8050
POLYGLOTKA_ANKI_MIN_COUNTS=5,3  # Format: known_count,learning_count
POLYGLOTKA_ANKI_FILTERS="deck:漢字 is:suspended"
```

### Development Workflow
1. Set `POLYGLOTKA_LR_DATA_DIR` to point to Language Reactor export directory
2. Use `poetry run python src/polyglotka/main.py` for rapid iteration
3. Run tests after changes: `poetry run pytest -v`
4. Access plots at configured `PLOTS_SERVER_URL` (auto-opens browser)