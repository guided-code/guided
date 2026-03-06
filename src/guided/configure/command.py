from typer import Typer

app = Typer(no_args_is_help=True)

@app.command()
def setup():
    print("Hello from guided!")

if __name__ == "__main__":
    app()
