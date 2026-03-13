import rich
import typer
from rich.table import Table

from guided.configure.config import save_config
from guided.configure.schema import Preference

app = typer.Typer(no_args_is_help=True, help="Manage user preferences.")


@app.command(name="list")
def list_preferences(ctx: typer.Context):
    """List all preferences."""
    config = ctx.obj
    if not config.preferences:
        rich.print("[yellow]No preferences set.[/yellow]")
        return
    table = Table("Key", "Value")
    for key, pref in sorted(config.preferences.items()):
        table.add_row(key, str(pref.value))
    rich.print(table)


@app.command()
def get(ctx: typer.Context, key: str):
    """Get a preference value."""
    config = ctx.obj
    if key not in config.preferences:
        rich.print(f"[red]Preference '{key}' not set.[/red]")
        raise typer.Exit(1)
    rich.print(config.preferences[key].value)


@app.command()
def set(ctx: typer.Context, key: str, value: str):
    """Set a preference value."""
    config = ctx.obj
    config.preferences[key] = Preference(key=key, value=value)
    save_config(config)
    rich.print(f"[green]Preference '{key}' set to '{value}'.[/green]")


@app.command()
def unset(ctx: typer.Context, key: str):
    """Remove a preference."""
    config = ctx.obj
    if key not in config.preferences:
        rich.print(f"[red]Preference '{key}' not set.[/red]")
        raise typer.Exit(1)
    del config.preferences[key]
    save_config(config)
    rich.print(f"[green]Preference '{key}' removed.[/green]")
