from typing import Optional

import ollama
import rich
import typer
from rich.console import Console

from guided.chat.actions import ActionContext, default_registry


def chat(
    ctx: typer.Context,
    model: Optional[str] = typer.Argument(default=None, help="Model name to chat with"),
):
    """Chat interactively with a model."""
    config = ctx.obj

    # Resolve model name
    if model is None:
        model_cfg = next((m for m in config.models.values() if m.is_default), None)
        if model_cfg is None:
            rich.print("[red]No model specified and no default model configured.[/red]")
            rich.print(
                "Run [bold]guide models set-default <name>[/bold] to set a default."
            )
            raise typer.Exit(1)
        model_name = model_cfg.name
        provider_key = model_cfg.provider
    elif model in config.models:
        model_cfg = config.models[model]
        model_name = model_cfg.name
        provider_key = model_cfg.provider
    else:
        # Treat as a bare model name; find an ollama provider to use
        model_name = model
        provider_key = next(
            (k for k, p in config.providers.items() if p.name == "ollama"), None
        )
        if provider_key is None:
            rich.print(f"[red]No provider found for model '{model}'.[/red]")
            raise typer.Exit(1)

    provider = config.providers.get(provider_key)
    if provider is None:
        rich.print(f"[red]Provider '{provider_key}' not found in config.[/red]")
        raise typer.Exit(1)

    client = ollama.Client(host=provider.base_url)
    messages = []
    registry = default_registry()

    rich.print(
        f"[bold]Chatting with[/bold] [cyan]{model_name}[/cyan] via [cyan]{provider.name}[/cyan]"
    )
    rich.print(
        "Type your message and press Enter. Leave blank or press Ctrl+C to exit."
    )
    rich.print("Type [cyan]/help[/cyan] for available actions.\n")

    console = Console()
    while True:
        try:
            console.out("\nYou:", style="dim", end="")
            user_input = typer.prompt("", prompt_suffix=" ")
        except (typer.Abort, KeyboardInterrupt, EOFError):
            rich.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input.strip():
            rich.print("[dim]Goodbye.[/dim]")
            break

        if user_input.strip().startswith("/"):
            action_context = ActionContext(
                config=config, messages=messages, registry=registry
            )
            should_exit = registry.dispatch(user_input.strip(), action_context)
            if should_exit:
                break
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            with console.status("[bold magenta]Thinking...", spinner="dots"):
                stream = client.chat(
                    model=model_name,
                    messages=messages,
                    stream=True,
                )
                # Eagerly fetch the first chunk so the spinner is shown while
                # waiting for the model to respond, then stop it before printing.
                chunks = list(stream)

            console.out("\nAssistant: ", style="dim", end="")
            full_response = []
            for chunk in chunks:
                content = chunk.message.content
                if content:
                    console.out(content, end="")
                    full_response.append(content)

            console.out("\n")
            messages.append({"role": "assistant", "content": "".join(full_response)})

        except Exception as e:
            rich.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
