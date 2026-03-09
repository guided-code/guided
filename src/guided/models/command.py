import typer
import rich
from rich.table import Table
import ollama

from guided.configure.config import load_config, save_config
from guided.configure.schema import Model

app = typer.Typer(no_args_is_help=True)


@app.command()
def list():
    config = load_config()

    table = Table("Name", "Provider", "Default", "Source")

    for m in config.models.values():
        table.add_row(m.name, m.provider, "yes" if m.is_default else "", "config")

    for provider in config.providers.values():
        if provider.name == "ollama":
            try:
                client = ollama.Client(host=provider.base_url)
                response = client.list()
                configured_names = set(config.models.keys())
                for model in response.models:
                    if model.model not in configured_names:
                        table.add_row(model.model, provider.name, "", "ollama")
            except Exception as e:
                rich.print(
                    f"[yellow]Warning: could not reach ollama at {provider.base_url}: {e}[/yellow]"
                )

    if table.row_count == 0:
        rich.print("[yellow]No models configured.[/yellow]")
        return

    rich.print(table)


@app.command()
def add(
    name: str,
    provider: str,
    default: bool = typer.Option(False, "--default", help="Set as the default model"),
):
    config = load_config()
    if name in config.models:
        rich.print(f"[red]Model '{name}' already exists.[/red]")
        raise typer.Exit(1)
    if default:
        for m in config.models.values():
            m.is_default = False
    config.models[name] = Model(name=name, provider=provider, is_default=default)
    save_config(config)
    rich.print(f"[green]Model '{name}' added.[/green]")


@app.command()
def remove(name: str):
    config = load_config()
    if name not in config.models:
        rich.print(f"[red]Model '{name}' not found.[/red]")
        raise typer.Exit(1)
    del config.models[name]
    save_config(config)
    rich.print(f"[green]Model '{name}' removed.[/green]")


@app.command(name="set-default")
def set_default(name: str):
    """Mark a model as the default."""
    config = load_config()
    if name not in config.models:
        rich.print(f"[red]Model '{name}' not found.[/red]")
        raise typer.Exit(1)
    for key, m in config.models.items():
        m.is_default = key == name
    save_config(config)
    rich.print(f"[green]Model '{name}' set as default.[/green]")


if __name__ == "__main__":
    app()
