---
name: jira
description: Retrieves Jira ticket and epic context using Atlassian CLI (acli) in read-only mode. Use when the user mentions Jira tickets (e.g., PROJECT-1234), asks for epic child tickets, needs outcomes/acceptance criteria summarized, or wants JQL-based ticket lists via `acli jira workitem view/search`.
allowed-tools: "Bash(acli:*), Read"
---

# Jira retrieval with `acli`

## Prerequisites

- **acli**: https://developer.atlassian.com/cloud/acli/guides/introduction/

```bash
which acli || echo "acli not installed: https://developer.atlassian.com/cloud/acli/guides/introduction/"
```

## Scope + defaults

- Default to **read-only** Jira access. Do not create/edit/transition Jira work items unless explicitly requested.
- Prefer **small, targeted** reads (specific fields / small ticket sets) over dumping full JSON for many tickets.
- When generating content that will be **pasted into Jira** (ticket descriptions, epic updates, comments), reference Jira tickets as **raw URLs** (no markdown link syntax), e.g.: `https://<your-instance>.atlassian.net/browse/PROJECT-1234`

## Quick start

### View a single ticket

```bash
acli jira workitem view PROJECT-1234
acli jira workitem view PROJECT-1234 --web     # open in browser
acli jira workitem view PROJECT-1234 --json    # structured extraction
```

### Search (JQL) for a set of tickets

```bash
acli jira workitem search --jql 'project = PROJECT AND status != Done ORDER BY updated DESC' --json
```

Common epic patterns (use whichever matches the Jira project configuration):

```bash
acli jira workitem search --jql 'parent = PROJECT-5678' --json
acli jira workitem search --jql '"Epic Link" = PROJECT-5679' --json
```

### Epic children: status vs comments

- `workitem search` lists **keys + status + summary** but not comments.
- To review **comments**, call `workitem view` per ticket with the `comment` field.
- Jira comments are returned as **Atlassian Document Format (ADF)** in JSON; summarize rather than pasting raw JSON.

### Extract PR links from Jira comments (ADF)

- Fetch: `acli jira workitem view PROJECT-1234 --json --fields 'summary,status,updated,comment,issuelinks'`
- Extract links: search JSON output for `github.com/<org>/<repo>/pull/<num>` patterns, then use `gh pr view` to confirm state.

## Field selection

```bash
# Minimal summary
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,assignee,reporter,priority,labels,components,fixVersions,description'

# Dependency context
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,issuelinks,subtasks'

# Comment signal (blockers/rollout state)
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,updated,comment,issuelinks'

# Custom fields / escape hatch
acli jira workitem view PROJECT-1234 --json --fields '*all'
```

## Epic → outcomes summary workflow

When asked "what are the outcomes of the tickets in this epic?":

1. **List child tickets** (pick `parent =` or `"Epic Link" =`).
2. **For each child ticket**, extract: outcome, acceptance criteria, user/maintainer impact, dependencies.
3. **Deduplicate** overlapping outcomes.
4. Produce a short outcomes inventory (1–2 bullets per ticket) and an aggregated deliverable candidate.

## Common failure modes + fixes

- **Field not allowed / not found**: remove the field; retry; only use `'*all'` when needed.
- **Too much output**: prefer `--fields` with a minimal set.
- **Epic child query returns nothing**: try the alternative epic pattern (`parent =` vs `"Epic Link" =`), or remove status filters.
- **Moved tickets**: Jira may redirect keys (e.g., `OLD-5652 → NEW-2834`). Treat the redirected key as canonical in notes.
- **Large epics**: fetch comments only for non-Done tickets or tickets updated in the review window.
