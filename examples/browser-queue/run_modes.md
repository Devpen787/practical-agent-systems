# Run modes

This pattern works because the run modes do different jobs.

## Preview

Show what would become a queue item before writing anything.

Useful when the drafting step is still noisy and you want to review candidates first.

## Enqueue

Write selected candidates into the queue as pending actions.

This is the handoff point between drafting and execution.

## Dry-run

Run the writer without browser actions.

Useful for checking queue handling, pacing rules, retry logic, and status updates without opening a live surface.

## Browser dry-run

Open the browser, navigate to the real target, and stop before submission.

Useful for answering the uncomfortable but important question: "Would this still work in the actual interface?"

## Live

Execute only after the earlier modes look clean.

This is where the queue stops being a draft and becomes a real action.
