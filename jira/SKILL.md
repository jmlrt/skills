---
name: jira
description: Retrieves Jira ticket and epic context using Atlassian CLI (acli) in read-only mode. Use when the user mentions Jira tickets (e.g., PROJECT-1234), asks for epic child tickets, needs outcomes/acceptance criteria summarized, or wants JQL-based ticket lists via `acli jira workitem view/search`.
allowed-tools: "Bash(acli:*), Read, Grep, Glob"
---

# Jira retrieval with `acli`

> **Configuration required**: Replace `{JIRA_BASE_URL}` with your Jira instance URL (e.g. `https://yourorg.atlassian.net`). Set it in your workspace `CLAUDE.md` / `AGENTS.md` for auto-pickup.

## Scope + defaults

- Default to **read-only** Jira access. Do not create/edit/transition Jira work items unless explicitly requested.
- Prefer **small, targeted** reads (specific fields / small ticket sets) over dumping full JSON for many tickets.
- When writing notes, follow any workspace-specific Jira link format. Common format:
  - `[PROJECT-1234 Short ticket title]({JIRA_BASE_URL}/browse/PROJECT-1234)`
- When generating content that will be **pasted into Jira** (ticket descriptions, epic updates, comments), reference Jira tickets as **raw URLs** (no markdown link syntax), e.g.: `{JIRA_BASE_URL}/browse/PROJECT-1234`

## Quick start

### View a single ticket

```bash
acli jira workitem view PROJECT-1234
```

Open in browser:

```bash
acli jira workitem view PROJECT-1234 --web
```

JSON for tooling / structured extraction:

```bash
acli jira workitem view PROJECT-1234 --json
```

### Search (JQL) for a set of tickets

```bash
acli jira workitem search --jql 'project = PROJECT AND status != Done ORDER BY updated DESC' --json
```

Common epic patterns (use whichever matches the Jira project configuration):

```bash
# Some projects model children via parent
acli jira workitem search --jql 'parent = PROJECT-5678' --json

# Others use "Epic Link"
acli jira workitem search --jql '"Epic Link" = PROJECT-5679' --json
```

### Epic children: status vs comments

- `workitem search` is great for listing **keys + status + summary**, but it's not enough for comment-based signal.
- To review **comments**, you must call `workitem view` per ticket with the `comment` field.
- Jira comments are returned as **Atlassian Document Format (ADF)** in JSON; treat them as "signal snippets" and summarize (don't paste raw JSON).

### Extract PR links from Jira comments (ADF)

When you need "comments + related PRs mentioned in comments":

- Fetch: `acli jira workitem view PROJECT-1234 --json --fields 'summary,status,updated,comment,issuelinks'`
- Extract links: look for ADF `inlineCard` URLs (often GitHub PRs). Practical approach: search the JSON output for patterns like `github.com/<org>/<repo>/pull/<num>` and then use `gh pr view <num> --repo <org>/<repo>` to confirm merged/closed state.

## Field selection (recommended defaults)

### Minimal summary (good for milestone review prep)

Goal: enough information to derive outcomes/deliverables without noise.

```bash
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,assignee,reporter,priority,labels,components,fixVersions,description'
```

### Dependency context

```bash
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,issuelinks,subtasks'
```

### Comment signal (last 1–3 comments)

Use when you need blockers/asks/rollout state from the latest discussion.

```bash
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,updated,comment,issuelinks'
```

### Custom fields / "field not found" escape hatch

- If `acli` rejects a field (common error: "field X not allowed"), remove it and retry.
- If you need custom fields (story points, confidence, etc.), fetch everything and then filter:

```bash
acli jira workitem view PROJECT-1234 --json --fields '*all'
```

## Epic → outcomes summary workflow (for deliverables / planning)

When asked "what are the outcomes of the tickets in this epic?":

1. **List child tickets** (pick `parent =` or `"Epic Link" =`).
2. **For each child ticket**, extract:
   - **Outcome**: what changes for users/consumers/maintainers when done
   - **Acceptance criteria** or implied "definition of done"
   - **User impact** and/or **maintainer impact**
   - **Dependencies** that affect reachability
3. **Deduplicate** overlapping outcomes across tickets.
4. Produce:
   - a **short "outcomes inventory"** (1–2 bullets per ticket, max)
   - an **aggregated deliverable candidate** (outcome-focused, measurable if possible)

## Common failure modes + fixes

- **Field not allowed / not found**: remove the field; retry; only use `'*all'` when needed.
- **Too much output**: prefer `--fields` with a minimal set; avoid dumping full JSON for many tickets.
- **Epic child query returns nothing**: try the alternative epic pattern (`parent =` vs `"Epic Link" =`), or remove status filters.
- **Moved tickets**: Jira may redirect keys (e.g., `OLD-5652 → NEW-2834`). Treat the redirected key as canonical in notes.
- **Large epics**: fetch comments only for (a) non-Done tickets and/or (b) tickets updated in the review window; otherwise you'll spend time parsing noise.
- **Buffered output in scripts**: if you script multi-ticket extraction, prefer `python3 -u` (or `print(..., flush=True)`) so progress logs stream and you can stop early if needed.
