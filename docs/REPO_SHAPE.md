# Public Repo Shape

## Goal

Turn a private multi-system agent repo into a public proof-of-work repo that is:

- easier to understand in under 5 minutes
- safer to share with employers and peers
- strong enough that someone can inspect the code and follow up

## Core repo story

The story is not:

- I use AI tools
- I built a lot of scripts
- I have a big personal repo

The story is:

- I build agent workflows that are reviewable
- I care about safety gates and evaluation
- I care about useful automation, not demo automation
- I know how to package systems so another person can inspect them

## Public artifacts

### `examples/agentops-lite`

Purpose:
- show governance and upgrade discipline for agents

Should include:
- example agent manifest
- example model policy
- example upgrade proposal
- example eval result
- short runner or validation script

Should demonstrate:
- stable contracts
- human approval
- evaluation before promotion

### `examples/browser-queue`

Purpose:
- show a browser-based workflow with explicit safety gates

Should include:
- queue schema
- one draft or pending action example
- dry-run behavior
- one execution script or stub

Should demonstrate:
- browser automation for real work
- no “fully autonomous” theater
- review before irreversible action

### `examples/support-check`

Purpose:
- show source-grounded research and support checking

Should include:
- a tiny sample source set
- a simple claim object
- evidence linking example
- a support-check example

Should demonstrate:
- source traceability
- support-aware drafting discipline
- how to avoid unsupported claims

## Public docs to include

At minimum:

- root `README.md`
- one architecture note
- one extraction plan
- one `WHY_THIS_EXISTS.md` style explanation if needed later

## What to optimize for

1. A reader should understand the repo in under 2 minutes.
2. A technical reviewer should find real structure, not marketing.
3. A hiring manager should see judgment and packaging ability, not chaos.
4. A collaborator should be able to say “I can see how this works.”

## What to avoid

- too many examples
- unclear boundaries between private and public systems
- giant config surfaces
- secrets or brittle local assumptions
- overclaiming what is production-ready
