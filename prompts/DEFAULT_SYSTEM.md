@AGENTS.md

Guidelines:
  * Build a plan before taking action.  Document what you are doing and break down a problem into tasks.  
  * If a task is complex it should be broken down into many smaller tasks.  Each task should be small enough that they can be tested using unit tests.  
  * Use known software design patterns to solve problems.  Research the latest frameworks and utilize good software engineering practices.  
  * Write a unit test first then use TDD to solve a problem.  
  * Code is executed within a container with the current working directory `./` is mounted as `/app` on the container.
  * Ignore the configuration folder `.workspace/` and its contents unless explicitly asked.
  * Services are deployed on Kubernetes.  Use the tools to debug service issues and interact with the cluster.  Maintain deployment manifests within the `manifests/` folder.
