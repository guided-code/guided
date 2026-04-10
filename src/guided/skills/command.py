import rich
import typer
from rich.table import Table

from guided.skills.library import (
    create_skill,
    discover_skills,
    is_valid_skill_name,
    remove_skill,
)

app = typer.Typer(no_args_is_help=True, help="Manage skills.")


@app.command()
def list(ctx: typer.Context):
    """List markdown skills in .guided/skills."""
    del ctx
    skills = discover_skills()

    if not skills:
        rich.print("[yellow]No skills found in .guided/skills.[/yellow]")
        return

    table = Table("Name", "Description", "Path")
    for skill in sorted(skills.values(), key=lambda s: s.name):
        table.add_row(f"[dim]{skill.name}[/dim]", skill.description, str(skill.path))

    rich.print(table)


@app.command()
def add(
    ctx: typer.Context,
    name: str,
    description: str = typer.Option(
        "", "--description", "-d", help="Skill description"
    ),
):
    """Create a markdown skill in .guided/skills/<name>/SKILL.md."""
    del ctx
    if not is_valid_skill_name(name):
        rich.print(
            "[red]Invalid skill name.[/red] Use letters, numbers, dashes, or underscores, and start with a letter."
        )
        raise typer.Exit(1)
    try:
        skill = create_skill(name=name, description=description)
    except FileExistsError:
        rich.print(f"[red]Skill '{name}' already exists.[/red]")
        raise typer.Exit(1)

    rich.print(f"[green]Skill '{name}' added.[/green]")
    rich.print(skill.path)


@app.command()
def remove(ctx: typer.Context, name: str):
    """Remove a markdown skill directory."""
    del ctx
    try:
        removed_path = remove_skill(name)
    except FileNotFoundError:
        rich.print(f"[red]Skill '{name}' not found.[/red]")
        raise typer.Exit(1)

    rich.print(f"[green]Skill '{name}' removed.[/green]")
    rich.print(removed_path)


if __name__ == "__main__":
    app()
