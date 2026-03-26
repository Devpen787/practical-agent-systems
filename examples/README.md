# Examples

These examples are meant to be:

- small
- inspectable
- representative

They should show the shape of the system clearly enough that a reader can understand the workflow without needing the private source repo.

Current examples:

- `agentops-lite`
- `browser-queue`
- `support-check`

Right now `agentops-lite` is the clearest place to start because it already shows the basic control loop:

- define the agent
- pin the policy
- write the proposed change down
- run the eval
- decide whether the change holds up
