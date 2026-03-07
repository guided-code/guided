from typer import Typer

app = Typer(no_args_is_help=True)


@app.command()
def list():
    print("Hello from guided!")


@app.command()
def add():
    print("Hello from guided!")


@app.command()
def remove():
    print("Hello from guided!")


if __name__ == "__main__":
    app()
