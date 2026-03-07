import typer
import rich
from rich.table import Table

from guided.configure.config import Model, load_config, save_config

app = typer.Typer(no_args_is_help=True)


@app.command()
def list():
    config = load_config()
    if not config.models:
        rich.print("[yellow]No models configured.[/yellow]")
        return
    table = Table("Name", "Provider")
    for m in config.models:
        table.add_row(m.name, m.provider)
    rich.print(table)


@app.command()
def add(name: str, provider: str):
    config = load_config()
    if any(m.name == name for m in config.models):
        rich.print(f"[red]Model '{name}' already exists.[/red]")
        raise typer.Exit(1)
    config.models.append(Model(name=name, provider=provider))
    save_config(config)
    rich.print(f"[green]Model '{name}' added.[/green]")


@app.command()
def remove(name: str):
    config = load_config()
    before = len(config.models)
    config.models = [m for m in config.models if m.name != name]
    if len(config.models) == before:
        rich.print(f"[red]Model '{name}' not found.[/red]")
        raise typer.Exit(1)
    save_config(config)
    rich.print(f"[green]Model '{name}' removed.[/green]")


if __name__ == "__main__":
    app()
