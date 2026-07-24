---
name: session-learnings
description: Extract recurring user corrections and tool failures from the current session, then make small, high-leverage updates to the appropriate guidance. Use when asked for session learnings, to reduce iteration, or to encode a newly discovered workflow or style constraint.
---

# Session Learnings

Turn repeated corrections and proven workflow discoveries into durable guidance so future sessions start closer to the desired result.

## Gather evidence

Use the current conversation as the primary source. Also inspect relevant diffs and files named by the user. If the context was compacted and local guidance identifies a transcript facility, retrieve only the missing sections.

Look for:

- Explicit user corrections or preferences.
- Tool failures, wrong syntax, permission constraints, or failed fallback paths.
- Work that had to be redone because a workflow step was missed.
- Stable ordering, placement, or project conventions.

If none are present, say that no updates are needed. Do not create guidance merely to produce a change.

## Decide what to retain

Write a short rule only when it is reusable, specific, and supported by the session. Drop one-offs and transient state.

| Learning | Home |
| --- | --- |
| Tool behavior, command syntax, or a repeatable tool workflow | The relevant skill or command guidance |
| Durable workflow shared across projects | User-level guidance |
| Repository or subsystem convention | The closest repository guidance |
| Personal communication preference or user context | The active agent's memory or personal guidance, when available |

Consult active-agent and repository guidance for the exact locations and capabilities available in the current environment. Prefer the narrowest scope that prevents repetition; do not duplicate the same rule across layers.

## Apply the learning

An explicit request for session learnings authorizes small, targeted updates to the selected guidance. Before editing, apply this filter:

- Is the rule useful beyond this one session?
- Does the selected file own this behavior?
- Is the wording a short default with a clear exception, if needed?

If the answer is no, omit the update or use a narrower home.

When updating guidance:

- Fix misleading instructions instead of adding competing workarounds.
- Preserve existing structure and local conventions.
- Keep additions to 1–6 bullets unless a concise procedural sequence is necessary.
- Add a verification step when a recurring failure is otherwise easy to repeat.

## Validate and report

Re-read every edited section. Return:

1. The learned rules and their rationale.
2. Each file changed and why it was the right scope.
3. Any candidate deliberately not retained.

## Common patterns

- Replace a wrong CLI example with the verified form rather than appending a warning.
- Capture the reason behind a placement or ordering correction, not just the requested position.
- Keep a command thin when its corresponding skill owns the full workflow.
- Keep public skills generic; route environment- or user-specific behavior to private or local guidance.
