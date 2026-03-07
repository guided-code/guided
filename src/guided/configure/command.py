import rich

from guided.configure.config import ensure_guided_home, load_config, save_config


def setup_configuration():
    home = ensure_guided_home()
    rich.print(f"[green]Guided home:[/green] {home}")

    config = load_config()
    save_config(config)
    rich.print(f"[green]Configuration loaded.[/green]")
