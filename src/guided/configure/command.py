import rich

from guided.configure.config import ensure_guided_home, get_default_config, save_config
from guided.configure.schema import Configuration


def setup_configuration(config: Configuration, overwrite_with_default: bool = False):
    home = ensure_guided_home()
    rich.print(f"[green]Guided home:[/green] {home}")

    if overwrite_with_default:
        # Use the default configuration instead of the provided one
        config = get_default_config()

    save_config(config)
    rich.print("[green]Configuration loaded.[/green]")
