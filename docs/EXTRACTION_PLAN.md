# Extraction Plan

## Source repo

Private source material currently lives in:

- `/Users/devinsonpena/Documents/AutoBots`

That repo is too broad to share directly. The public repo should extract only the parts that work as clean proof of work.

## Strongest extractable pieces

### 1. AgentOps contracts and governance pattern

Candidate sources:

- `/Users/devinsonpena/Documents/AutoBots/agentops/README.md`
- `/Users/devinsonpena/Documents/AutoBots/AGENTS.md`
- `/Users/devinsonpena/Documents/AutoBots/docs/AGENTOPS_INTEGRATION.md`
- `/Users/devinsonpena/Documents/AutoBots/docs/program_board.md`

What to extract:

- the control-plane idea
- the stable contracts
- the promotion / eval rule
- the human-review stance

What to leave behind:

- repo-specific operational details
- references to personal systems unless renamed generically

### 2. Browser queue and safety pattern

Candidate sources:

- `/Users/devinsonpena/Documents/AutoBots/README.md`
- `/Users/devinsonpena/Documents/AutoBots/scripts/run.sh`
- `/Users/devinsonpena/Documents/AutoBots/scripts/run_writer.sh`
- `/Users/devinsonpena/Documents/AutoBots/out/actions_queue.json`

What to extract:

- queue shape
- dry-run / live split
- browser workflow pattern
- retry / dead-letter idea

What to leave behind:

- personal X profile details
- any workflow tied to personal posting or private accounts

### 3. Source-grounded research pattern

Candidate sources:

- `/Users/devinsonpena/Documents/AutoBots/proofmap/README.md`
- `/Users/devinsonpena/Documents/AutoBots/docs/research_os_status.md`

What to extract:

- source ingestion idea
- support-check principle
- supported-claims retrieval concept
- visible benchmark and holdout discipline

What to leave behind:

- app-shell scaffolding that does not help explain the idea
- internal roadmap noise

## First public milestone

The first public version should be small.

Ship:

- `agentops-lite`
- `browser-queue`
- one `support-check` example

Do not ship:

- full private repo history
- every runner
- every internal report
- personal infrastructure

## Success criteria

The repo is ready to link from the website when:

1. the README stands on its own
2. one or two examples are runnable or at least inspectable
3. the repo feels curated rather than extracted in a hurry
4. the public story is stronger than simply saying “I use AI agents”
