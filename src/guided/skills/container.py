from pathlib import Path

import docker

CONTAINER_IMAGE = "alpine:latest"
MOUNT_PATH = "/workspace"


def read_file(path: str, cwd: Path | None = None) -> str:
    """Read a file in a container where the current working folder is mounted as /workspace."""
    cwd = (cwd or Path.cwd()).resolve()
    client = docker.from_env()
    command = "cat " + path + ""

    host_config = client.create_host_config(
        binds={str(cwd): {"bind": MOUNT_PATH, "mode": "rw"}}
    )
    container = client.create_container(
        image=CONTAINER_IMAGE,
        command=command,
        working_dir=MOUNT_PATH,
        volumes=[MOUNT_PATH],
        host_config=host_config,
    )
    container_id = container["Id"]
    try:
        client.start(container_id)
        exit_code = client.wait(container_id)
        output = client.logs(container_id, stdout=True, stderr=True)
        if isinstance(output, bytes):
            output = output.decode()
        if exit_code != 0:
            return output.strip() or f"Command failed with exit code {exit_code}"
        return output
    finally:
        client.remove_container(container_id, force=True)
