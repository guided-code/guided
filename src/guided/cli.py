import rich
import typer
from pydantic import ValidationError

import guided
from guided.chat.command import chat
from guided.configure.command import setup_configuration
from guided.configure.config import load_config
from guided.models.command import app as models_app
from guided.providers.command import app as providers_app

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
def configure(ctx: typer.Context, overwrite_with_default: bool = False):
    setup_configuration(ctx.obj, overwrite_with_default=overwrite_with_default)


app.add_typer(models_app, name="models")
app.add_typer(providers_app, name="providers")
app.command()(chat)


@app.command()
def version():
    rich.print("Version: ", guided.__version__)


def run():
    """
    Exported Python package script
    """
    app()


if __name__ == "__main__":
    run()
