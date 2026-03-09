from typing import Optional

import ollama
import rich
import typer


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

    rich.print(
        f"[bold]Chatting with[/bold] [cyan]{model_name}[/cyan] via [cyan]{provider.name}[/cyan]"
    )
    rich.print(
        "Type your message and press Enter. Leave blank or press Ctrl+C to exit."
    )
    rich.print("Use /exit to stop chatting.\n")

    while True:
        try:
            user_input = typer.prompt("You", prompt_suffix=": ")
        except (typer.Abort, KeyboardInterrupt, EOFError):
            rich.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input.strip():
            rich.print("[dim]Goodbye.[/dim]")
            break

        # Check for slash commands
        if user_input.strip().startswith("/"):
            command = user_input.strip()
            if command == "/exit":
                rich.print("[dim]Goodbye.[/dim]")
                break
            else:
                rich.print(f"[red]Unknown command: {command}[/red]")
                continue

        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat(model=model_name, messages=messages)
            assistant_message = response.message.content
            messages.append({"role": "assistant", "content": assistant_message})
            rich.print(f"\n[bold cyan]Assistant[/bold cyan]: {assistant_message}\n")
        except Exception as e:
            rich.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
