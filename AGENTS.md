# AGENTS.md

Guided is a CLI tool designed to amplify the work of engineers by providing the scaffolding necessary to build great software with agentic AI resources.

Projects are designed to operate in Kubernetes in containerized environments.  A workspace is a project root folder that is associated with one more more container images.  

## Commands

Scripts can be executed from the project base folder. All scripts require `uv` to be installed.

```bash
bin/guide     # Run CLI from source code
bin/test      # Run all tests (uv run pytest tests/)
bin/lint      # Lint and format (ruff check --fix + ruff format on src/)
```

The `guide configure` command accepts an `--use_default` flag to reset the configuration to the default settings.

## Architecture

`guided` is a Python CLI tool built with **Typer** and **Rich**. The entry point is `guided.cli:run` (registered as the `guide` binary).

This tool is designed utilizes an opinionated approach to managing a Kubernetes project and favors convention over configuration.  

### Module layout (`src/guided/`)

- `cli.py` — Root Typer app; registers subcommand groups (`models`, `providers`, `skills`, `workspace`) and top-level commands (`configure`, `version`, `chat`)
- `configure/` — Configuration subsystem
  - `schema.py` — Pydantic models for configuration validation (`Provider`, `Model`, `Skill`, `Configuration`); enforces single default model
  - `config.py` — Load/save YAML config at `~/.guided/config.yaml` (overridable via `GUIDED_HOME` env var); default config seeds an ollama provider
  - `command.py` — `guide configure` command
- `providers/` — `guide providers` subcommands (list/add/remove providers in config)
- `models/` — `guide models` subcommands (list/add/remove/set-default models; also discovers models live from ollama)
- `skills/` — `guide skills` subcommands (list/add/remove skills in config)
- `workspace/` — `guide workspace` subcommands for managing local project workspaces
  - `command.py` — `init` (creates `.workspace/` with `decisions/`, `transcripts/`, `context/` subdirs) and `info` commands
  - `schema.py` — `WorkspaceConfig` Pydantic model (name, version, created_at)
- `chat/` — `guide chat [model]` interactive chat command
  - `command.py` — Streams responses from ollama; loads AGENTS.md context from `./AGENTS.md`, `.workspace/AGENTS.md`, or `.workspace/context/AGENTS.md`
  - `actions.py` — In-chat slash command system: `Action` ABC, `ActionContext`, `ActionRegistry`, built-in `ExitAction` (`/exit`, `/quit`, `/bye`, `/q`) and `HelpAction` (`/help`)
- `agents/` — stub (not registered in CLI)

### Container image layout (`/usr/src`)

A project's current working directory is expected to be mounted within `/workspace` in the container.  


### Workspace layout (`.workspace/`)

A workspace configuration folder is created at `.workspace/` when a project is initialized.  

- `config.yaml` — Workspace configuration (name, version, created_at)
- `decisions/` — Decision records
- `transcripts/` — Chat transcripts
- `context/` — Context files


### Config file

Config is stored as YAML at `~/.guided/config.yaml`. The schema is `Configuration`. The default model is selected via the `is_default` flag on `Model`.

The default configuration includes an Ollama provider pointing to `http://localhost:11434`.


### Actions

Actions are slash commands such as `/clear`, `/help`, `/exit`, etc. which are run during interactive chat sessions

### Skills

Skills are tools the LLM can use. When a skill is executed an invocation object `SkillExecution` captures results.  Skills are registered in the `skills` modules.

Default skills include:

- `search_web_text` — Query the Internet for information
- `request_web` — Read a Web page from the Internet



## Tests

Unit tests should be written to confirm functionality. Tests are organized in the `tests` folder and tests using the `typer.testing.CliRunner` are in the `tests/cli` folder.

Run a single test file:

```bash
bin/test tests/test_models_command.py
```

Run a single test by name:

```bash
bin/test tests/test_models_command.py::test_list_empty_no_ollama
```

Running tests with LLM support, which are normally skipped

```bash
bin/test --with-llm tests/
```

### Debugging

Use the env variable `LOGGING_LEVEL` to set the Python logging level.

Use the env variable `DEBUG=1` to turn on debugging mode.


## Documentation

Features are documented in the `docs` folder.  Keep this folder up to date and reference it to reflect changes.  
