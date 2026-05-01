@AGENTS.md

Guidelines:
  * Build a plan before taking action.  Document what you are doing and break down a problem into tasks.  
  * If a tasks should be broken down into action items and small enough that they can be tested using unit tests.  
  * Write a unit test first then use TDD to solve a problem.  
  * Code is executed within a container with the current working directory mounted as `/workspace`.
  * Ignore the `.workspace/` folder and its contents unless explicitly asked.
  * Services are deployed on Kubernetes.  Use the tools to debug service issues and interact with the cluster.  Maintain deployment manifests within the `manifests/` folder.
