# Guided

## What is Guided?

Guided is a CLI tool designed to amplify the work of engineers using AI.  

The idea is simple. Avoid spaghetti code and create maintainable code by making a solid scaffold.  

- Provide a framework to execute in parallel
- Leverage local LLMs with instruction following and thinking
- Use tools in a containerized environment with Kubernetes
- Log everything and make it reversible

## Philosophy

We believe that while work can be automated, engineers are an important piece of the puzzle when it comes to managing software.

While automation and artificial intelligence can be leveraged to write code quickly, managing the direction of a long term project will require a deeper level of understanding.

Properly planned code can go a long way to not only solve problems scaling but also increase velocity and maintainability.

The goal of Guided is to provide a framework for engineers to manage the direction of a project while leveraging AI to execute the work.

## Usage

We recommend using [Ollama](https://ollama.com/); install it if you have not already. Install a model which supports tool calling and thinking.

Use [uv](https://docs.astral.sh/uv/) to manage the Python virtual environment.  

Install the CLI tool.  

Run the installation script (e.g. - always check an installation script by downloading and reading it first)

```bash
curl "https://raw.githubusercontent.com/guided-code/guided/refs/heads/main/bin/install" | sh -h
```

Configure your environment by running:

```bash
guide configure
```

Start a TUI and chat directly

```bash
guide chat
```

Or use a command line interface

```bash
echo "What files are in this directory?" | guide chat
```

## Agents

Agents can be either third party agents or local agents. The default settings are to use local agents. 

## Tasks

Tasks are services that can be run by the agents. Tasks can be configured on a workspace or at a global level.

Before executing a task you should fully understand the task and the potential impact it may have on the project.

## Documentation

Find documentation in the [docs](docs/index.md) folder.

## Contributing

We encourage you to contribute to Guided. Guided is about building great tools to enable engineers to build more. Join us! [Read about contributing](CONTRIBUTING.md)

## License

Guided is licensed under the [MIT License](https://opensource.org/licenses/MIT).
