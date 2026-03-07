import typer
import rich

import guided
from guided.configure.command import setup_configuration
from guided.models.command import app as models_app

app = typer.Typer(
    no_args_is_help=True,
    help="Guided is a CLI tool designed to amplify the work of engineers by providing the scaffolding necessary to build great software with agentic AI resources.",
)

@app.command()
def configure():
    setup_configuration()

app.add_typer(models_app, name="models")

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
