import rich

from guided.configure.config import ensure_guided_home, save_config
from guided.configure.schema import Configuration


def setup_configuration(config: Configuration):
    home = ensure_guided_home()
    rich.print(f"[green]Guided home:[/green] {home}")

    save_config(config)
    rich.print("[green]Configuration loaded.[/green]")
