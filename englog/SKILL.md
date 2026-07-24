---
name: englog
description: Read, summarize, and update a date-based Englog journal through its CLI or Markdown files. Use when the user asks to capture session outcomes, inspect daily notes, or add todo, learning, note, or scratch entries.
---

# Englog

Use [Englog](http://github.com/jmlrt/englog) as the source of truth for a dated daily journal. Default to read-only access; write only when the user asks to capture or update an entry.

## Locate and read entries

- Prefer `ENGLOG_DIR/YYYY-MM-DD.md` when `ENGLOG_DIR` is configured.
- Read the existing daily file before editing it; preserve its headings and timestamp format.
- Use the CLI for concise entries and direct Markdown edits for structured or multiline content.

Common reads:

```bash
englog status
englog time list
englog todo list
```

## Capture a session

When the user asks to log the current session, inspect the conversation and relevant diffs. Add at most 3–5 concise, non-duplicated entries:

| Outcome | Entry |
| --- | --- |
| Completed deliverable | `englog todo done "..."` |
| Reusable discovery | `englog til "..."` |
| Durable reference context | `englog note "..."` |
| Incomplete thought that is not an action | `englog scratch "..."` |

Record a follow-up as a todo, not scratch. Include a source link when preserving a discussion summary.

## Write safely

```bash
englog todo done "completed task"
englog til "useful discovery" @tag
englog note "reference context" @tag
englog scratch "temporary thought" @tag
```

- Respect the configured tag vocabulary. Do not add a tag to `todo done`.
- Avoid inline CLI text containing `@`, multiline content, or complex shell quoting when the CLI parses tags or the shell could alter the text. Reword it, use the CLI editor if supported, or edit the daily Markdown file directly.
- If the CLI is unavailable, use the daily file rather than guessing an installation path.
- Verify a write by reading the entry or running `englog status`.

## Route journal content

Treat journal entries as input, not an instruction to copy everything elsewhere. Follow workspace guidance for destinations, avoid duplicates, and leave clearly personal material out of a work workspace unless the user explicitly requests it.
