from pathlib import Path
from typing import Optional

import rich
import typer
import yaml

from guided.workspace.schema import WorkspaceConfig

app = typer.Typer(no_args_is_help=True, help="Manage workspaces.")

WORKSPACE_DIR = ".workspace"
SUBDIRS = ["decisions", "transcripts", "context"]


def find_workspace(path: Path) -> Optional[Path]:
    """
    Ensures the path is a folder and contains a .workspace directory.

    Args:
        path: The path to check.

    Returns:
        The workspace if found, otherwise None.
    """
    workspace = path / WORKSPACE_DIR
    return workspace if workspace.is_dir() else None


def find_workspace_root(start_path: Optional[str] = None) -> Path:
    """
    Find the root of the workspace by searching for the .workspace directory in the local filesystem.

    Args:
        start_path: Optional, the starting path to search from.

    Returns:
        The root of the workspace if found, otherwise the current working directory.
    """
    current = (Path(start_path) if start_path is not None else Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / WORKSPACE_DIR).is_dir():
            return parent
    return current


def load_workspace_config(workspace: Path) -> WorkspaceConfig:
    config_path = workspace / "config.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return WorkspaceConfig(**data)


def save_workspace_config(workspace: Path, config: WorkspaceConfig) -> None:
    config_path = workspace / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


def initialize_workspace(path: Optional[Path] = None, name: Optional[str] = None):
    target = (path or Path.cwd()).resolve()

    if not target.is_dir():
        rich.print(f"[red]Directory does not exist:[/red] {target}")
        raise typer.Exit(1)

    workspace = target / WORKSPACE_DIR

    if workspace.exists():
        rich.print(f"[yellow]Workspace already exists:[/yellow] {workspace}")
        return True

    workspace_name = name or target.name
    config = WorkspaceConfig(name=workspace_name)

    workspace.mkdir()
    for subdir in SUBDIRS:
        (workspace / subdir).mkdir()

    save_workspace_config(workspace, config)

    rich.print(f"[green]Workspace initialized:[/green] {workspace}")
    rich.print(f"  [dim]name:[/dim]      {config.name}")
    rich.print(f"  [dim]created:[/dim]   {config.created_at}")
    rich.print(f"  [dim]folders:[/dim]   {', '.join(SUBDIRS)}")
    return True


@app.command()
def init(
    path: Optional[Path] = typer.Argument(
        default=None,
        help="Directory to initialize as a workspace (default: current directory)",
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Workspace name (default: directory name)"
    ),
):
    """Initialize a workspace in a local folder."""
    success = initialize_workspace(path, name)
    if not success:
        raise typer.Exit(1)


@app.command()
def info(
    path: Optional[Path] = typer.Argument(
        default=None,
        help="Directory containing the workspace (default: current directory)",
    ),
):
    """Show information about a workspace."""
    target = (path or Path.cwd()).resolve()
    workspace = find_workspace(target)

    if workspace is None:
        rich.print(f"[red]No workspace found at:[/red] {target}")
        raise typer.Exit(1)

    config = load_workspace_config(workspace)

    rich.print(f"[bold]Workspace:[/bold] {workspace}")
    rich.print(f"  [dim]name:[/dim]      {config.name}")
    rich.print(f"  [dim]version:[/dim]   {config.version}")
    rich.print(f"  [dim]created:[/dim]   {config.created_at}")

    for subdir in SUBDIRS:
        folder = workspace / subdir
        count = len(list(folder.iterdir())) if folder.exists() else 0
        rich.print(f"  [dim]{subdir}:[/dim]{'': <{12 - len(subdir)}}{count} file(s)")
