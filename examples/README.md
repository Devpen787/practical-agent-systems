# Examples

These examples are meant to be:

- small
- inspectable
- representative

They should show the shape of the system clearly enough that a reader can understand the workflow without needing extra context.

Current examples:

- `agentops-lite`
- `browser-queue`
- `support-check`
- `technocore-ios-agent`

`agentops-lite` is the clearest place to start for the basic control loop:

- define the agent
- pin the policy
- write the proposed change down
- run the eval
- decide whether the change holds up

`technocore-ios-agent` shows a different boundary: private signing authority remains local while code and sanitized evidence stay public and independently verifiable.
