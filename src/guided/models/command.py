import ollama
import rich
import typer
from rich.table import Table

from guided.configure.config import save_config
from guided.configure.schema import Model

app = typer.Typer(no_args_is_help=True)


@app.command()
def list(ctx: typer.Context):
    config = ctx.obj

    table = Table("Name", "Provider", "Default", "Source")

    # Sort models from configuration
    sorted_config_models = sorted(config.models.values(), key=lambda m: m.name)
    for m in sorted_config_models:
        table.add_row(m.name, m.provider, "yes" if m.is_default else "", "config")

    # Add Ollama discovered models
    ollama_models = []
    for provider in config.providers.values():
        if provider.name == "ollama":
            try:
                client = ollama.Client(host=provider.base_url)
                response = client.list()
                configured_names = set(config.models.keys())
                for model in response.models:
                    if model.model not in configured_names:
                        ollama_models.append(model)
            except Exception as e:
                rich.print(
                    f"[yellow]Warning: could not reach ollama at {provider.base_url}: {e}[/yellow]"
                )

    # Sort Ollama models alphabetically
    sorted_ollama_models = sorted(ollama_models, key=lambda m: m.model)
    for model in sorted_ollama_models:
        table.add_row(model.model, "ollama", "", "ollama")

    if table.row_count == 0:
        rich.print("[yellow]No models configured.[/yellow]")
        return

    rich.print(table)


@app.command()
def add(
    ctx: typer.Context,
    name: str,
    provider: str,
    default: bool = typer.Option(False, "--default", help="Set as the default model"),
):
    config = ctx.obj
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
def remove(ctx: typer.Context, name: str):
    config = ctx.obj
    if name not in config.models:
        rich.print(f"[red]Model '{name}' not found.[/red]")
        raise typer.Exit(1)
    del config.models[name]
    save_config(config)
    rich.print(f"[green]Model '{name}' removed.[/green]")


@app.command(name="set-default")
def set_default(ctx: typer.Context, name: str):
    """Mark a model as the default."""
    config = ctx.obj
    if name not in config.models:
        rich.print(f"[red]Model '{name}' not found.[/red]")
        raise typer.Exit(1)
    for key, m in config.models.items():
        m.is_default = key == name
    save_config(config)
    rich.print(f"[green]Model '{name}' set as default.[/green]")


if __name__ == "__main__":
    app()
