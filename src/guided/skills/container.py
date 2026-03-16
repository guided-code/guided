from pathlib import Path
from typing import Optional
import docker

from guided.workspace.command import find_workspace_root

CONTAINER_IMAGE = "alpine:latest"
MOUNT_PATH = "/workspace"
WORKING_DIR = "/workspace"


def exec_command(command: str, working_dir: Optional[str] = WORKING_DIR) -> str:
    """
    Execute a command in a container where the current working folder is mounted as /workspace.

    Args:
        command: The command to execute.
        working_dir: Optional, the current working directory within the host container

    Returns:
        The output of the command.
    """
    workspace_root = find_workspace_root()
    client = docker.from_env()

    host_config = client.api.create_host_config(
        binds={str(workspace_root): {"bind": MOUNT_PATH, "mode": "rw"}}
    )
    container = client.api.create_container(
        image=CONTAINER_IMAGE,
        command=command,
        working_dir=working_dir,
        volumes=[MOUNT_PATH],
        host_config=host_config,
    )
    container_id = container["Id"]
    try:
        client.api.start(container_id)
        exit_code = client.api.wait(container_id)
        output = client.api.logs(container_id, stdout=True, stderr=True)
        if isinstance(output, bytes):
            output = output.decode()
        if exit_code != 0:
            return output.strip() or f"Command failed with exit code {exit_code}"
        return output
    finally:
        client.api.remove_container(container_id, force=True)


def list_files(folder_path: Optional[str] = None) -> str:
    """
    List folders in a specified directory.

    Args:
        folder_path: A relative path within workspace

    Returns:
        The output of the command.
    """
    work_dir = find_workspace_root()
    target_path = Path(work_dir / folder_path).resolve()

    if not target_path.is_relative_to(work_dir):
        return f"Error: Path {folder_path} is outside the workspace"

    if not target_path.exists():
        return f"Error: Path {folder_path} does not exist"

    if not target_path.is_dir():
        return f"Error: Path {folder_path} is not a directory"

    try:
        return "\n".join(sorted(p.name for p in target_path.iterdir()))
    except Exception as e:
        return f"Failed to list folders in {folder_path}: {e}"


def read_file(file_path: str) -> str:
    """
    Read a file in the workspace folder.  Intended for reading text files which are compatible with the model context.

    Args:
        path: The path to the file.

    Returns:
        The content of the file.
    """
    work_dir = find_workspace_root()
    target_path = Path(work_dir / file_path).resolve()

    if not target_path.is_relative_to(work_dir):
        return f"Error: Path `{file_path}` is outside the workspace"

    if not target_path.exists():
        return f"Error: Path `{file_path}` does not exist"

    if not target_path.is_file():
        return f"Error: Path `{file_path}` is not a file"

    try:
        return f"```@{file_path}\n{target_path.read_text()}\n```"
    except Exception as e:
        return f"Failed to read {file_path}: {e}"


def write_file(file_path: str, content: str) -> str:
    """
    Write a file to the workspace folder.

    Args:
        file_path: The path to the file.
        content: The content of the file.

    Returns:
        The output of the command.
    """
    work_dir = find_workspace_root()
    target_path = Path(work_dir / file_path).resolve()

    if not target_path.is_relative_to(work_dir):
        return f"Error: Path `{file_path}` is outside the workspace"

    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        target_path.write_text(content)
        return f"Successfully wrote to `{file_path}`"
    except Exception as e:
        return f"Failed to write to `{file_path}`: {e}"
