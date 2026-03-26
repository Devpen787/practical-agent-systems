# Practical Agent Systems

`practical-agent-systems` is a small public repo for reviewable agent workflows.

It focuses on three things:

- agent operations with explicit evaluation and upgrade discipline
- browser-based workflows with approval gates
- source-grounded research patterns that keep claims tied to evidence

The goal is not to show the biggest possible agent stack. The goal is to show patterns that are actually useful in real work and easy to inspect.

## What is in this repo

This repo is organized around three example tracks:

- [`examples/agentops-lite`](./examples/agentops-lite)
- [`examples/browser-queue`](./examples/browser-queue)
- [`examples/support-check`](./examples/support-check)

Each example is meant to be small, readable, and practical.

## Why this repo exists

A lot of agent projects are either:

- toy demos with no real workflow constraints
- vague “AI automation” claims with nothing inspectable behind them
- large internal systems that are too messy to share directly

This repo is meant to be the opposite:

- narrow enough to understand quickly
- concrete enough to inspect
- honest about human review, failure handling, and boundaries

## What the examples are meant to show

### Agent operations

How to treat agent workflows like systems that need:

- manifests
- policies
- upgrade proposals
- evaluation before promotion

### Browser queue workflows

How to structure browser automation so it can:

- stage actions
- support dry runs
- separate drafting from execution
- keep irreversible actions behind review

### Support checking

How to keep research and drafting grounded by making it easier to answer:

- what does this claim rely on
- what evidence supports it
- where is the support weak

## What this repo is not

It is not:

- a personal operating system dump
- a fully autonomous agent platform
- a benchmark theater project
- a promise that every example is production-ready

## Current status

The repo is in scaffold phase. The structure is in place and the next step is to turn the first example into a clean public artifact.

## Start here

If you want the quickest read:

1. open [`examples/agentops-lite`](./examples/agentops-lite)
2. then read [`docs/REPO_SHAPE.md`](./docs/REPO_SHAPE.md)

That is the shortest path to understanding what the repo is trying to do.
