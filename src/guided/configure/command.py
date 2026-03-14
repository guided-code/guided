import ollama
import rich

from guided.configure.config import ensure_guided_home, get_default_config, save_config
from guided.configure.schema import Configuration, Model


def setup_configuration(config: Configuration, overwrite_with_default: bool = False):
    home = ensure_guided_home()
    rich.print(f"[green]Guided home:[/green] {home}")

    if overwrite_with_default:
        # Use the default configuration instead of the provided one
        config = get_default_config()

    # Look for an available model to load using the ollama provider
    provider = config.providers.get("ollama")
    if provider:
        try:
            client = ollama.Client(host=provider.base_url)
            response = client.list()
            if response.models:
                # Get the first available model
                first_model = response.models[0].model
                assert isinstance(first_model, str)

                # Check if there are no default models currently
                has_default = any(m.is_default for m in config.models.values())

                if first_model not in config.models:
                    config.models[first_model] = Model(
                        name=first_model, provider="ollama", is_default=not has_default
                    )
                    rich.print(
                        f"[green]Discovered and added model '{first_model}' from Ollama.[/green]"
                    )
                elif not has_default:
                    config.models[first_model].is_default = True

        except Exception as e:
            rich.print(
                f"[yellow]Warning: Could not discover models from Ollama at {provider.base_url}: {e}[/yellow]"
            )

    save_config(config)
    rich.print("[green]Configuration loaded.[/green]")
