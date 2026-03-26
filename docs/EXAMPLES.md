# Examples

This repo is being built around a few small examples rather than one large system.

## Why

Smaller examples are easier to:

- inspect
- explain
- reuse
- discuss in interviews or technical follow-up

They are also a better public surface than linking a large private operating repo directly.

## Planned example set

### 1. `agentops-lite`

A minimal example of reviewable agent operations.

Intended contents:

- an example agent manifest
- an example model policy
- an example upgrade proposal
- an example eval result

### 2. `browser-queue`

A minimal example of a browser workflow with safety gates.

Intended contents:

- queue schema
- pending action example
- dry-run / live split
- failure or retry handling pattern

### 3. `support-check`

A minimal example of source-grounded support checking.

Intended contents:

- source snippet
- claim object
- evidence link example
- support-check example

## Standard for inclusion

An example should only be added when it is:

- understandable on its own
- safe to share publicly
- stronger as a proof artifact than as a private note
