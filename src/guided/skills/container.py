from pathlib import Path
from typing import Optional
import docker

from guided.workspace.command import find_workspace_root

DEFAULT_CONTAINER_IMAGE = "alpine:latest"
MOUNT_PATH = "/app"
WORKING_DIR = "/app"


def build_container_image(
    tag: str,
    dockerfile_path: Optional[str] = "Dockerfile",
) -> str:
    """
    Builds a container image from a Dockerfile in the workspace.

    Args:
        tag: The image name and optional tag (e.g. "myapp:latest").
        dockerfile_path: Optional relative path to the Dockerfile within the workspace.
                         Defaults to "Dockerfile" at the workspace root.

    Returns:
        A success message with the image tag, or an error message.
    """
    workspace_root = find_workspace_root()
    dockerfile = Path(workspace_root / (dockerfile_path or "Dockerfile")).resolve()

    if not dockerfile.is_relative_to(workspace_root):
        return "Error: Dockerfile path is outside the workspace"

    if not dockerfile.exists():
        return f"Error: Dockerfile not found at {dockerfile}"

    client = docker.from_env()
    try:
        _, logs = client.images.build(
            path=str(workspace_root),
            dockerfile=str(dockerfile),
            tag=tag,
            rm=True,
        )
        for entry in logs:
            if "error" in entry:
                return f"Build failed: {entry['error'].strip()}"
        return f"Successfully built image {tag}"
    except docker.errors.BuildError as e:
        return f"Build failed: {e}"
    except Exception as e:
        return f"Failed to build container image: {e}"


def exec_command(
    command: str,
    working_dir: Optional[str] = WORKING_DIR,
    container_image: str = DEFAULT_CONTAINER_IMAGE,
) -> str:
    """
    Executes a command in the container where the current working folder is mounted as /workspace.

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
        image=container_image,
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


def read_file(
    file_path: str, start_line: int = 0, end_line: Optional[int] = None
) -> str:
    """
    Read a file in the workspace folder.  Read specific lines while debugging.

    Args:
        path: The path to the file.
        start_line: Optional, the line number to start reading from (0-indexed).
        end_line: Optional, the line number to stop reading at (exclusive).

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
        lines = []
        with target_path.open("r") as f:
            lines = f.readlines()

        selected_lines = (
            lines[start_line:end_line] if end_line is not None else lines[start_line:]
        )
        return f"```@{file_path}\n{selected_lines}\n```"
    except Exception as e:
        return f"Failed to read {file_path}: {e}"


def write_file(file_path: str, content: str) -> str:
    """
    Write a file to the workspace folder.

    Args:
        file_path: A relative file path within the workspace
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
