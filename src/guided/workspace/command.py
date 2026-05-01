import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import rich
import typer
import yaml
from prompt_toolkit.shortcuts import confirm

import guided
from guided.workspace.schema import WorkspaceConfig

app = typer.Typer(no_args_is_help=True, help="Manage workspaces.")

WORKSPACE_DIR = ".workspace"
SUBDIRS = ["decisions", "transcripts", "context"]


def machine_info() -> List[str]:
    """Returns list of strings with basic information about the local machine."""
    import platform

    system_info = platform.uname()
    return [
        system_info.system,
        system_info.node,
        system_info.release,
        system_info.version,
        system_info.machine,
        system_info.processor,
        sys.platform,
        sys.thread_info.name,
        sys.thread_info.lock,
        sys.version,
    ]


def workspace_key() -> str:
    """A unique hash generated to identify the local system to differentiate between workspaces on
    different machines"""
    import hashlib

    workspace_info = machine_info()
    workspace_info.extend(guided.__version__)

    return hashlib.sha256("".join(workspace_info).encode()).hexdigest()[:16]


def get_workspace(base_path: Path) -> Optional[Path]:
    """
    Gets workspace path from a base path

    Args:
        base_path: The path to check.

    Returns:
        The workspace if found, otherwise None.
    """
    workspace_path = base_path / WORKSPACE_DIR
    return workspace_path if workspace_path.is_dir() else None


def find_workspace_root(start_path: Optional[str] = None) -> Path:
    """
    Find the root, or base_path, of the workspace by searching for the .workspace directory in the local filesystem.  Base
    path of workspace must be an updated workspace.

    Args:
        start_path: Optional, the starting path to search from.

    Returns:
        The root of the workspace if found, otherwise the current working directory.
    """
    nested_location = (
        Path(start_path) if start_path is not None else Path.cwd()
    ).resolve()
    for current_base in [nested_location, *nested_location.parents]:
        current_workspace = current_base / WORKSPACE_DIR
        current_config = current_workspace / "config.yaml"
        if current_workspace.is_dir() and current_config.is_file():
            config = load_workspace_config(current_workspace)
            if config.workspace_key == workspace_key():
                return current_base

    # Use starting location; cwd as default
    return nested_location


def load_workspace_config(workspace_path: Path) -> WorkspaceConfig:
    config_path = workspace_path / "config.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return WorkspaceConfig(**data)


def save_workspace_config(workspace_path: Path, config: WorkspaceConfig) -> None:
    config.updated_at = datetime.now(timezone.utc).isoformat()
    config_path = workspace_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=True)


def initialize_workspace(
    path: Optional[Path] = None,
    name: Optional[str] = None,
):
    target = (path or Path.cwd()).resolve()

    if not target.is_dir():
        rich.print(f"[red]Directory does not exist:[/red] {target}")
        raise typer.Exit(1)

    workspace_path = target / WORKSPACE_DIR

    # Existing path
    if workspace_path.exists():
        rich.print(f"[yellow]Workspace exists:[/yellow] {workspace_path}")

        # Confirm workspace_key matches if config exists
        config_path = workspace_path / "config.yaml"
        if config_path.is_file():
            config = load_workspace_config(workspace_path)
            if config.workspace_key != workspace_key():
                if config.workspace_key is None:
                    rich.print(
                        "[yellow]Notice:[/yellow] The CLI tool has been upgraded. Updating workspace configuration."
                    )
                    config.workspace_key = workspace_key()
                    save_workspace_config(workspace_path, config)
                    return True
                else:
                    rich.print(
                        "[red]Error:[/red] Run `guided workspace update` to update the workspace configuration first."
                    )
                    raise typer.Exit(1)

        return True

    # New workspace
    else:
        workspace_name = name or target.name
        config = WorkspaceConfig(name=workspace_name, workspace_key=workspace_key())

        if confirm(
            message=f"Confirm create a new workspace at: {workspace_path}: ",
            suffix="(y/[n]) ",
        ):
            workspace_path.mkdir()
            for subdir in SUBDIRS:
                (workspace_path / subdir).mkdir()

            # Initialize SYSTEM.md from DEFAULT_SYSTEM.md template
            default_system = (
                Path(__file__).parent.parent.parent.parent
                / "prompts"
                / "DEFAULT_SYSTEM.md"
            )
            if default_system.exists():
                workspace_system = workspace_path / "SYSTEM.md"
                workspace_system.write_text(default_system.read_text())

            save_workspace_config(workspace_path, config)

            rich.print(f"[green]Workspace initialized:[/green] {workspace_path}")
        else:
            rich.print("[yellow]Workspace initialization cancelled.[/yellow]")
            raise typer.Exit(0)

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
    workspace_path = get_workspace(target)

    if workspace_path is None:
        rich.print(f"[red]Error: No workspace found at:[/red] {target}")
        raise typer.Exit(1)

    config = load_workspace_config(workspace_path)

    rich.print(f"[bold]Workspace:[/bold] {workspace_path}")
    rich.print(f"  [dim]name:[/dim]      {config.name}")
    rich.print(f"  [dim]version:[/dim]   {config.version}")
    rich.print(f"  [dim]created:[/dim]   {config.created_at}")

    for subdir in SUBDIRS:
        folder = workspace_path / subdir
        count = len(list(folder.iterdir())) if folder.exists() else 0
        rich.print(f"  [dim]{subdir}:[/dim]{'': <{12 - len(subdir)}}{count} file(s)")


@app.command()
def update(
    path: Optional[Path] = typer.Argument(
        default=None,
        help="Directory containing the workspace (default: current directory)",
    ),
):
    """Update the workspace configuration to match the current machine."""
    target = (path or Path.cwd()).resolve()
    workspace_path = get_workspace(target)

    if workspace_path is None:
        rich.print(f"[red]Error: No workspace found at:[/red] {target}")
        raise typer.Exit(1)

    config = load_workspace_config(workspace_path)
    config.workspace_key = workspace_key()
    save_workspace_config(workspace_path, config)

    rich.print(f"[green]Workspace updated:[/green] {workspace_path}")
