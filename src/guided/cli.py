import logging
from typing import Optional

import rich
import typer
from pydantic import ValidationError

import guided
from guided.chat.command import run_chat
from guided.configure.command import setup_configuration
from guided.configure.config import load_config
from guided.environment import get_logging_level, is_debug
from guided.models.command import app as models_app
from guided.preferences.command import app as preferences_app
from guided.providers.command import app as providers_app
from guided.skills.command import app as skills_app
from guided.workspace.command import app as workspace_app

if is_debug():
    logging.basicConfig(level=get_logging_level())
logger = logging.getLogger("guided.core")

app = typer.Typer(
    no_args_is_help=True,
    help="Guided is a CLI tool designed to amplify the work of engineers by providing the scaffolding necessary to build great software with agentic AI resources.",
)


@app.callback()
def validate_config(ctx: typer.Context):
    try:
        ctx.obj = load_config()
    except ValidationError as e:
        rich.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def configure(
    ctx: typer.Context,
    overwrite_with_default: bool = typer.Option(
        False, "--use_default", help="Reset configuration to default settings"
    ),
):
    """Initialize or update the Guided configuration file."""
    setup_configuration(ctx.obj, overwrite_with_default=overwrite_with_default)


@app.command()
def chat(
    ctx: typer.Context,
    model: Optional[str] = typer.Argument(default=None, help="Model name to chat with"),
):
    """Chat interactively with a model, or pipe text via stdin for a single response."""
    run_chat(ctx.obj, model=model)


app.add_typer(models_app, name="models")
app.add_typer(preferences_app, name="preferences")
app.add_typer(providers_app, name="providers")
app.add_typer(skills_app, name="skills")
app.add_typer(workspace_app, name="workspace")


@app.command()
def version():
    """Show the current version of Guided."""
    rich.print("Version: ", guided.__version__)


def run():
    """
    Exported Python package script
    """
    app()


if __name__ == "__main__":
    run()
