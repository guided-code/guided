# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Guided is a CLI tool designed to amplify the work of engineers by providing the scaffolding necessary to build great software with agentic AI resources.

## Commands

All scripts require `uv` to be installed.

```bash
bin/test      # Run all tests (uv run pytest tests/)
bin/lint      # Lint and format (ruff check --fix + ruff format on src/)
```

Run a single test file:
```bash
bin/test tests/test_models_command.py
```

Run a single test by name:
```bash
bin/test tests/test_models_command.py::test_list_empty_no_ollama
```

## Architecture

`guided` is a Python CLI tool built with **Typer** and **Rich**. The entry point is `guided.cli:run` (registered as the `guide` binary).

### Module layout (`src/guided/`)

- `cli.py` — Root Typer app; registers subcommand groups (`models`, `providers`) and top-level commands (`configure`, `version`)
- `configure/` — Configuration subsystem
  - `schema.py` — Pydantic models for configuration validation
  - `config.py` — Load/save YAML config at `~/.guided/config.yaml` (overridable via `GUIDED_HOME` env var); default config seeds an ollama provider
  - `command.py` — `guide configure` command
- `providers/` — `guide providers` subcommands (list/add/remove providers in config)
- `models/` — `guide models` subcommands (list/add/remove models; also discovers models live from ollama)
- `agents/` — `guide agents` subcommands (stub, not yet implemented)
- `tools/` — Tool definitions (stub)

### Config file

Config is stored as YAML at `~/.guided/config.yaml`. The schema is `Config`.  The default model is selected as the `default` attribute in the Models dictionary.  

### Testing patterns

Tests use `typer.testing.CliRunner` to invoke CLI commands and `unittest.mock.patch` to mock `load_config`/`save_config`. Tests live in `tests/` and do not require any running services.
