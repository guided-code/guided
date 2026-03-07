import typer
import rich
from rich.table import Table

from guided.configure.config import Provider, load_config, save_config

app = typer.Typer(no_args_is_help=True)


@app.command()
def list():
    config = load_config()
    if not config.providers:
        rich.print("[yellow]No providers configured.[/yellow]")
        return
    table = Table("Name", "Base URL")
    for p in config.providers:
        table.add_row(p.name, p.base_url)
    rich.print(table)


@app.command()
def add(name: str, base_url: str):
    config = load_config()
    if any(p.name == name for p in config.providers):
        rich.print(f"[red]Provider '{name}' already exists.[/red]")
        raise typer.Exit(1)
    config.providers.append(Provider(name=name, base_url=base_url))
    save_config(config)
    rich.print(f"[green]Provider '{name}' added.[/green]")


@app.command()
def remove(name: str):
    config = load_config()
    before = len(config.providers)
    config.providers = [p for p in config.providers if p.name != name]
    if len(config.providers) == before:
        rich.print(f"[red]Provider '{name}' not found.[/red]")
        raise typer.Exit(1)
    save_config(config)
    rich.print(f"[green]Provider '{name}' removed.[/green]")


if __name__ == "__main__":
    app()
