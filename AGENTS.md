# Repository Guidelines

## Project Structure & Module Organization
- Core package lives under `src/polyglotka`; `main.py` exposes the CLI entry points registered in `pyproject.toml`.
- `common/` holds shared config helpers (see `src/polyglotka/common/config.py`), while `importer/` loads Language Reactor and Migaku exports, and `plots/` renders analytics dashboards.
- Command implementations are grouped in subpackages such as `simple_commands/` and `draft/`. Tests mirror this layout in `tests/`, with fixtures and samples under `tests/testing_data/`.
- Media assets for docs and UI reference reside in `media/`. Keep new assets lightweight and reference them from Markdown instead of embedding binaries in code.

## Build, Test, and Development Commands
- `poetry install` sets up the Python 3.13 environment and installs the CLI entry point.
- `poetry run polyglotka plots --help` previews CLI options; prefer running commands this way so dependencies resolve inside Poetry’s virtualenv.
- `poetry run pytest` executes the full suite with verbose output (`-v` is configured). Use `poetry run pytest -m smoke` for quick checks.
- `poetry run coverage run -m pytest && poetry run coverage report` tracks coverage, honoring omit rules in `pyproject.toml`.

## Coding Style & Naming Conventions
- Format code with Black (`poetry run black .`), respecting the 110-character line length and preserved string quotes. Keep imports sorted manually; no isort config is present.
- Use snake_case for functions and variables, PascalCase for classes, and kebab-case for CLI flags. New modules should follow existing directory naming (e.g., `src/polyglotka/new_feature/`).
- Target Python 3.13, add type hints where practical, and favor pure functions over script-style top-level code.

## Testing Guidelines
- Add tests alongside features in `tests/`. Name files `test_<feature>.py` and functions `test_<condition>`.
- Reuse pytest fixtures and sample exports from `tests/testing_data/` when possible, documenting new fixtures with brief docstrings.
- Ensure new behavior has at least one smoke test marker if it affects core commands.

## Commit & Pull Request Guidelines
- Mirror existing history: short, lowercase, present-tense summaries (e.g., `adjust plots layout`).
- Reference related issues, describe testing performed, and attach CLI output or screenshots for user-facing changes.
- Keep PRs focused; call out configuration or migration steps so maintainers can reproduce locally.

## Configuration Tips
- Prefer environment variables prefixed with `POLYGLOTKA_` when sharing reproducible setups. For updates that change defaults (e.g., cache paths), document them in `README.md`.
- Avoid committing personal exports; use anonymized samples in `tests/testing_data/` instead.
