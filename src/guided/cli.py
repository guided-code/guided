import typer
import rich

from guided.configure.command import app as configure_app

app = typer.Typer(help="Guided is a CLI tool designed to amplify the work of engineers by providing the scaffolding necessary to build great software with agentic AI resources.")

app.add_typer(configure_app, name="configure")

@app.command()
def version():
    import importlib.metadata
    rich.print("Version: ", importlib.metadata.version("guided"))

def run():
    """
    Exported Python package script
    """
    app()

if __name__ == "__main__":
    run()
