# Repository Guidelines

## Project Structure & Module Organization
Code lives in `src/polyglotka`, grouped by domain: `common` holds shared config, console helpers, and exceptions; `plots` and `kanji` expose CLI entry points; `lr_importer` contains Language Reactor data adapters. Dash assets and figures sit under `plots`. Tests belong in `tests/` and should mirror the module layout (e.g., `tests/test_lr_importer.py` for importer logic). Keep experimental notebooks or spikes inside `src/polyglotka/junk` so they stay isolated from production code.

## Build, Test, and Development Commands
Install dependencies with `poetry install`. Launch the CLI via `poetry run polyglotka <COMMAND>` where commands include `PLOTS`, `KANJI`, and `ANKI`; pass overrides as flags (`--lr-data-dir=/path`). During development, use `poetry run python src/polyglotka/main.py PLOTS` for quick iteration. Run tests with `poetry run pytest -v`; add `-m smoke` to target quick checks. Start the Dash server by calling `poetry run polyglotka PLOTS` and visiting the configured `PLOTS_SERVER_URL`.

## Coding Style & Naming Conventions
Target Python 3.13, type annotate public functions, and keep imports sorted within stdlib/third-party/local groups. Follow the configured Black profile (`line-length = 110`, `skip-string-normalization = true`) and ensure docstrings explain side effects or configuration knobs. Use `snake_case` for functions and modules, `PascalCase` for classes and enums, and uppercase for constants and environment-driven settings. Prefer raising `UserError` for user-facing CLI validation failures.

## Testing Guidelines
Pytest is the default; place fixtures in `tests/conftest.py` if needed. Name tests after behavior (e.g., `test_loads_language_reactor_items`). Cover new CLI flags and config validation, and add regression cases when touching parsers in `lr_importer`. Aim for high coverage on branches that mutate external data, and fail fast when mocks replace filesystem calls.

## Commit & Pull Request Guidelines
Commits in this repo stay short and imperative (`Refactor kanji`, `fix y_data`). Reference the affected module in the subject where possible. Pull requests should include: a clear problem statement, a summary of key changes, testing notes (`poetry run pytest`), and any screenshots of plots or Dash UI updates. Link related issues or TODOs directly in the description so reviewers can trace context.

## Configuration Tips
Runtime settings load from `.env` via `pydantic-settings`. Prefix variables with `POLYGLOTKA_` (e.g., `POLYGLOTKA_LR_DATA_DIR=/data/language-reactor`). Validate overrides locally before committing, and document non-default values in the PR so deployers can replicate your environment.
