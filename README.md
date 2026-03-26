# Practical Agent Systems

I like building systems that make complicated work feel simpler.

This repo is a small public proof surface for that idea in agent form.

It is where I am packaging a few patterns I keep coming back to:

- agent operations that can be reviewed instead of “trusted”
- browser workflows that stage actions before they execute them
- research flows that keep claims tied to evidence

The point is not to show the largest possible agent stack. The point is to show a few patterns that are useful, inspectable, and honest about where human judgment still matters.

## What is in this repo

This repo is organized around three example tracks:

- [`examples/agentops-lite`](./examples/agentops-lite)
- [`examples/browser-queue`](./examples/browser-queue)
- [`examples/support-check`](./examples/support-check)

Each one is meant to stay small, readable, and real.

`agentops-lite` and `browser-queue` now have real inspectable files behind them instead of placeholder descriptions.

## Why this repo exists

A lot of agent work online falls into one of three buckets:

- toy demos with no real workflow constraints
- vague “AI automation” claims with nothing inspectable behind them
- large internal systems that are too messy to share directly

I wanted something that lands in the gap between those three:

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

## Start here

If you want the quickest read:

1. open [`examples/agentops-lite`](./examples/agentops-lite)
2. then read [`docs/REPO_SHAPE.md`](./docs/REPO_SHAPE.md)

That is the shortest path to understanding what this repo is trying to prove.
