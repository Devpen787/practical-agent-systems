# Practical Agent Systems

Open-source proof of work for agent and automation systems that are meant to be inspected, reviewed, and used in real workflows.

This repo is not a dump of my private operating systems. It is a smaller public artifact built to show how I think about:

- human-in-the-loop automation
- browser-based workflows
- source-grounded research systems
- evaluation and upgrade discipline
- agents that are useful in practice, not just impressive in demos

## Why this exists

Most agent projects either stop at toy demos or hide the real workflow behind vague claims. I wanted a public surface that makes the important parts inspectable:

- what the system does
- what it refuses to do automatically
- how it is reviewed
- how upgrades are evaluated
- what makes it useful in real work

The private repo behind some of this work is broader and more operational. This public repo is intentionally narrower. It exists to show the patterns cleanly.

## What will live here

This repo will be built around three public proof artifacts.

### 1. Reviewable agent operations

A lightweight control-plane pattern for:

- agent manifests
- model policies
- upgrade proposals
- evaluation results
- vendor-watch inputs

The point is simple: agent systems should not be upgraded by intuition alone.

### 2. Browser workflow automation

A small browser-driven workflow that does real work without pretending full autonomy is always the goal.

Examples of the pattern:

- digest and draft workflows
- approval queues
- browser execution with safety gates
- dry-run before live actions

### 3. Source-grounded research

A stripped research workflow that shows how claims, evidence, and support checking can stay reviewable instead of turning into black-box summarization.

This is the part most people describe vaguely. I want the structure to be visible.

## Design rules

This repo should feel:

- inspectable
- minimal
- useful
- honest about boundaries

It should not feel like:

- a personal dump
- a secret internal repo accidentally made public
- a benchmark theater project
- an AI-hype landing page

## Planned public structure

```text
practical-agent-systems/
├── README.md
├── docs/
│   ├── REPO_SHAPE.md
│   └── EXTRACTION_PLAN.md
├── examples/
│   ├── agentops-lite/
│   ├── browser-queue/
│   └── support-check/
└── assets/
```

## What stays private

The private systems behind this repo include broader operating surfaces, live workflows, and personal infrastructure that do not belong in a public artifact.

This repo should not expose:

- personal job-search automation
- live posting pipelines
- private profiles or credentials
- internal-only glue code
- rough experiments that add noise instead of proof

## Current status

Scaffold phase. The next step is to extract and package the first public examples cleanly from the private systems they came from.
