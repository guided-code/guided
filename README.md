Guided
---------

What is Guided?  

Guided is a CLI tool designed to amplify the work of engineers by providing the scaffolding necessary to build great software with agentic AI resources.

Guided leverages containerized environments and provides tools to build workflows in parallel, geared towards separating concerns for greater maintainability and scalability.  

Changes to a project are managed in a containerized environment associated with a Git worktree.  Project level details are managed in a workspace.  

Features:

- CLI tool to manage the development lifecycle of a project
- Multiple agent management
- Containerization of the development environment
- Testing tools
- Planning tools


## Philosophy

We believe that while work can be automated, engineers are the important piece of the puzzle.  And while automation and artificial intelligence can perform a tremendous amount of work, engineers understand what is being doine and ultimately are able to guide the direction of a project and utilize these tools to build better and better products.  


## How to use Guided?

Planning is the important part of the puzzle.  

In the same way that spaghetti code, a result of poor planning, is difficult to maintain and extend, poorly planned AI generated code will be difficult to maintain and extend.  The challenge of poorly planned code leads to exponential increases in time spent engineering.  Properly planned code can not only scale to solve larger and larger problems but also can be maintained and produce higher velocity over the lifetime of a project.  

Use workspaces to manage a project.  Workspaces are composed of stages.  Each stage represents a set of changes, or commits, in a codebase and is tagged deliberately as a Git tag using source control.  

A changelog is used to track the changes across different stages of a project.  

Additionally, a compaction process is used to review the current state of the project and determine if the project can be simplified or decisions and their reversals can be removed.  


## Usage

Install the CLI tool.

Run the installation script (e.g. - always check an installation script by downloading and reading it first)

```bash
curl "https://raw.githubusercontent.com/henrytseng/guided/refs/heads/main/bin/install" | sh -h
```

Configure your environment by running:

```bash
guide configure
```

Start a TUI and chat directly

```
guide chat
```

Or use a command line interface

```
echo "What files are in this directory?" | guide chat
```


## Agents

Agents can be either third party agents or local agents.  The default settings are to use local agents.  The recommendation is to use local agents.  


## Tasks

Tasks are services that can be run by the agents.  Tasks can be configured on a workspace or at a global level.  

Before executing a task you should fully understand the task and the potential impact it may have on the project.  


## Documentation

Find documentation in the [docs](docs/index.md) folder.


## Contributing

We encourage you to contribute to Guided. Guided is about building great tools to enable engineers to build more. Join us!

## License

Guided is licensed under the [MIT License](https://opensource.org/licenses/MIT).
