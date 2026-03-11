import rich
import typer
from rich.table import Table

from guided.configure.config import save_config
from guided.configure.schema import Skill

app = typer.Typer(no_args_is_help=True, help="Manage skills.")


@app.command()
def list(ctx: typer.Context):
    """List configured skills."""
    config = ctx.obj

    if not config.skills:
        rich.print("[yellow]No skills configured.[/yellow]")
        return

    table = Table("Name", "Type", "Description")
    for skill in sorted(config.skills.values(), key=lambda s: s.name):
        table.add_row(skill.name, skill.type, skill.description)

    rich.print(table)


@app.command()
def add(
    ctx: typer.Context,
    name: str,
    type: str,
    description: str = typer.Option(
        ..., "--description", "-d", help="Skill description"
    ),
):
    """Add a new skill."""
    config = ctx.obj
    if name in config.skills:
        rich.print(f"[red]Skill '{name}' already exists.[/red]")
        raise typer.Exit(1)
    config.skills[name] = Skill(name=name, type=type, description=description)
    save_config(config)
    rich.print(f"[green]Skill '{name}' added.[/green]")


@app.command()
def remove(ctx: typer.Context, name: str):
    """Remove a skill."""
    config = ctx.obj
    if name not in config.skills:
        rich.print(f"[red]Skill '{name}' not found.[/red]")
        raise typer.Exit(1)
    del config.skills[name]
    save_config(config)
    rich.print(f"[green]Skill '{name}' removed.[/green]")


if __name__ == "__main__":
    app()
