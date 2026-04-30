@AGENTS.md

Guidelines:
  * Commands are executed within a container with the current working directory mounted as `/workspace`.
  * Ignore the `.workspace/` folder and its contents unless explicitly asked.
  * Services are deployed using Kubernetes and can be interacted with using tools
  * Write a Dockerfile to build image(s) as necessary and a set of manifest files `manifests/` to deploy
