import typer
import rich
from rich.table import Table

from guided.configure.config import save_config
from guided.configure.schema import Provider

app = typer.Typer(no_args_is_help=True, help="Manage providers.")


@app.command()
def list(ctx: typer.Context):
    """List configured providers."""
    config = ctx.obj
    if not config.providers:
        rich.print("[yellow]No providers configured.[/yellow]")
        return
    table = Table("Name", "Base URL")
    for p in config.providers.values():
        table.add_row(p.name, p.base_url)
    rich.print(table)


@app.command()
def add(ctx: typer.Context, name: str, base_url: str):
    """Add a provider to the configuration."""
    config = ctx.obj
    if name in config.providers:
        rich.print(f"[red]Provider '{name}' already exists.[/red]")
        raise typer.Exit(1)
    config.providers[name] = Provider(name=name, base_url=base_url)
    save_config(config)
    rich.print(f"[green]Provider '{name}' added.[/green]")


@app.command()
def remove(ctx: typer.Context, name: str):
    """Remove a provider from the configuration."""
    config = ctx.obj
    if name not in config.providers:
        rich.print(f"[red]Provider '{name}' not found.[/red]")
        raise typer.Exit(1)
    del config.providers[name]
    save_config(config)
    rich.print(f"[green]Provider '{name}' removed.[/green]")


if __name__ == "__main__":
    app()
