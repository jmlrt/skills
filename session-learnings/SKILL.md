---
name: session-learnings
description: Extract recurring user corrections and tool failures from the current session, then make small, high-leverage updates to the appropriate guidance. Use when asked for session learnings, to reduce iteration, or to encode a newly discovered workflow or style constraint.
---

# Session Learnings

## Gather evidence

Use the current conversation as the primary source. Look for:

- Explicit user corrections or preferences.
- Tool failures, wrong syntax, or permission constraints.
- Work that had to be redone because a workflow step was missed.

If none are present, say so. Do not create guidance merely to produce a change.

## Decide what to retain

Apply KISS/YAGNI before writing anything. A learning only earns a place in guidance if it passes **all** of:

1. **Recurring** — likely to come up again, not a one-session quirk.
2. **Non-obvious to an agent** — would the agent encounter this as a surprise, or can it be inferred from standard docs, normal error output, or the tool's default behavior? Environment-specific constraints (sandbox quirks, proxy TLS, denied paths) qualify; generic CLI usage and basic git hygiene don't.
3. **Scoped to the target file** — local guidance (repo `CLAUDE.md`, `CLAUDE.local.md`) may include repo-specific content; global guidance (`~/.claude/CLAUDE.md`, skills, commands) must apply across repos, not just the current project.
4. **Not already self-describing** — the error message or tool output already explains the fix clearly; no standing rule needed.

**Reject** a candidate when it is:
- A niche edge case unlikely to recur (e.g. one specific API field, one rare CLI flag combination).
- Verbose enough to need a long explanation — if it can't be stated in 1–2 lines, it's probably too situational.
- Already covered by the tool's own docs, error output, or a skill that owns that domain.
- Standard practice that any engineer would apply without a reminder.

When in doubt, leave it out. A shorter guidance file is more likely to be read and followed.

| Learning | Home |
| --- | --- |
| Tool behavior, command syntax, or repeatable workflow | The relevant skill or command guidance |
| Durable workflow shared across projects | User-level guidance (CLAUDE.md) |
| Repository or subsystem convention | The closest repository guidance |
| Personal preference or user context | Claude memory |

Prefer the narrowest scope that prevents repetition; do not duplicate across layers.

Resolve a skill's source with `readlink` before editing it. Never put employer-specific details in skills from a
public repo; keep them in user-level guidance or a private skill instead.

## Apply the learning

Before editing, confirm: is the rule useful beyond this session and does the selected file own this behavior? If not, use a narrower home or omit.

When updating guidance:

- Fix misleading instructions instead of appending competing workarounds.
- Preserve existing structure and local conventions.
- Keep additions to 1–6 bullets.

## Report

Return: (1) the learned rules and rationale, (2) each file changed and why, (3) any candidate deliberately not retained.
