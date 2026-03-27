# Repo Shape

This repo is intentionally small.

The point is not to present a complete system. The point is to make a few reusable workflow patterns easy to inspect.

## Structure

```text
practical-agent-systems/
├── README.md
├── docs/
│   ├── REPO_SHAPE.md
│   └── EXAMPLES.md
└── examples/
    ├── agentops-lite/
    ├── browser-queue/
    └── support-check/
```

## Principles

Each example should be:

- small enough to understand quickly
- concrete enough to inspect without guesswork
- honest about what is automated and what still needs review

## Example roles

### `agentops-lite`

Shows a lightweight control-plane pattern for:

- agent manifests
- model policies
- upgrade proposals
- eval results

### `browser-queue`

Shows a workflow pattern for:

- staged actions
- dry-run versus live execution
- approval before irreversible browser actions

### `support-check`

Shows a research pattern for:

- claims
- evidence links
- support checking
- grounded review

## What success looks like

A good example in this repo should let a reader understand:

- what problem it solves
- what the workflow looks like
- where review happens
- why the pattern is useful outside a toy demo
