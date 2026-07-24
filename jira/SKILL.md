---
name: jira
description: "Retrieve Jira ticket and epic context, and create comments when explicitly requested, using the Atlassian CLI (`acli`). Use when the user mentions Jira tickets (e.g., PROJECT-1234), asks for epic child tickets, needs outcomes/acceptance criteria summarized, or wants JQL-based ticket lists via `acli jira workitem view/search`."
allowed-tools: "Bash(acli:*), Bash(grep:*), Bash(jq:*), Read"
argument-hint: [PROJECT-ticket or epic-key]
---

# Jira retrieval with `acli`

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

### Search field limitations

`workitem search --fields` only allows a subset of fields:
- **Allowed**: `key, summary, description, status, assignee, reporter, issuetype, priority, labels`
- **NOT allowed**: `created, resolutiondate, parent, subtasks, issuelinks, comment, *all, *navigable`

For fields that search cannot return, use `workitem view` per ticket. This means bulk export workflows always require per-ticket view calls for dates, relationships, and comments.

### Epic children: status vs comments

- `workitem search` lists **keys + status + summary** but not comments.
- To review **comments**, call `workitem view` per ticket with the `comment` field.
- Jira comments are returned as **Atlassian Document Format (ADF)** in JSON; summarize rather than pasting raw JSON.

### Extract PR links from Jira comments (ADF)

- Fetch: `acli jira workitem view PROJECT-1234 --json --fields 'summary,status,updated,comment,issuelinks'`
- Extract links: search JSON output for `github.com/<org>/<repo>/pull/<num>` patterns, then use `gh pr view` to confirm state.

## Field selection

**Minimal summary:**
```bash
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,assignee,reporter,priority,labels,components,fixVersions,description'
```

**Dependency context:**
```bash
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,issuelinks,subtasks'
```

**Comment signal (blockers/rollout state):**
```bash
acli jira workitem view PROJECT-1234 --json --fields 'summary,status,updated,comment,issuelinks'
```

**Custom fields (escape hatch):**
```bash
acli jira workitem view PROJECT-1234 --json --fields '*all'
```

## Epic → outcomes summary workflow

When asked "what are the outcomes of the tickets in this epic?":

1. **List child tickets** (pick `parent =` or `"Epic Link" =`).
2. **For each child ticket**, extract: outcome, acceptance criteria, user/maintainer impact, dependencies.
3. **Deduplicate** overlapping outcomes.
4. Produce a short outcomes inventory (1–2 bullets per ticket) and an aggregated deliverable candidate.

## Real-world workflow: Fetch epic outcomes

**Goal**: Summarize what an epic will deliver.

```bash
# 1. Find epic child tickets
EPIC="PROJECT-5678"
acli jira workitem search --jql "parent = $EPIC" --json | \
  jq -r '.[].key' > /tmp/tickets.txt

# 2. For each ticket, extract outcome and acceptance criteria
while read ticket; do
  acli jira workitem view "$ticket" --json --fields \
    'summary,description,status,assignee' | \
    jq '{key: .key, summary: .fields.summary, status: .fields.status.name}'
done < /tmp/tickets.txt

# 3. Optional: extract PR links from comments
acli jira workitem view $EPIC --json --fields 'comment,issuelinks' | \
  jq -r '.fields.comment[]? | .body' | \
  grep -oE 'github.com/[^/]+/[^/]+/pull/[0-9]+' || true
```

## Creating comments

**Default: plain text via `--body`** — use this for short notes with no links and no structure. No temp file needed.

```bash
acli jira workitem comment create --key "PROJECT-1234" --body "Simple plain text comment"
```

**Use ADF (`--body-file`) whenever the comment contains**: links (plain URLs are not clickable in Jira Cloud), headings, code blocks, nested lists, bold/inline code. Wiki markup (`h2.`, `{code}`, etc.) is silently ignored by Jira Cloud — ADF is the only way to get real formatting and clickable links.

**Temp file location**: write the ADF JSON to a temporary file in the current workspace and delete it after posting.

```bash
# Formatted comment — write locally, post, clean up
acli jira workitem comment create --key "PROJECT-1234" --body-file .tmp-jira-comment.json
rm .tmp-jira-comment.json

# Update the last comment from the same author
acli jira workitem comment create --key "PROJECT-1234" --edit-last --body-file .tmp-jira-comment.json
rm .tmp-jira-comment.json
```

**ADF formatting reference** (write JSON to a file, pass via `--body-file`):
- Root: `{"version": 1, "type": "doc", "content": [...]}`
- Heading: `{"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "..."}]}`
- Code block: `{"type": "codeBlock", "attrs": {"language": "bash"}, "content": [{"type": "text", "text": "..."}]}`
- Paragraph: `{"type": "paragraph", "content": [{"type": "text", "text": "..."}]}`
- Inline code: `{"type": "text", "text": "...", "marks": [{"type": "code"}]}`
- Bold: `{"type": "text", "text": "...", "marks": [{"type": "strong"}]}`
- Link: `{"type": "text", "text": "label", "marks": [{"type": "link", "attrs": {"href": "https://..."}}]}`
- Bullet list: `{"type": "bulletList", "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [...]}]}]}`
- Ordered list: `{"type": "orderedList", "attrs": {"order": 1}, "content": [...]}`

## Updating ticket metadata in markdown documentation

Use when syncing project docs (e.g. workstream epic files) with current Jira state.

### Standard ticket section format

```markdown
### PROJECT-1234 Ticket Title

- **Ticket ID:** [PROJECT-1234](https://<your-instance>.atlassian.net/browse/PROJECT-1234)
- **Parent/Epic:** [PROJECT-1000 Epic Name](https://<your-instance>.atlassian.net/browse/PROJECT-1000)
- **Status:** Backlog
- **Assignee:** Name
- **Sprint:** Sprint Name
- **Fix version:** Feature 2026-01
- **Due date:** None
- **Priority:** Medium
- **Story Points:** 3
- **Original estimate:** 3d
- **Subtasks:** None
- **Link work items:**
  - blocks:
    - https://<your-instance>.atlassian.net/browse/PROJECT-1001 (Ticket Title)
  - is blocked by:
    - https://<your-instance>.atlassian.net/browse/PROJECT-1002 (Ticket Title)
```

Custom-field IDs vary by Jira instance. Use `--fields '*all'` to discover them when needed.

### Workflow: update metadata

```bash
# 1. Find all ticket IDs in a markdown file
grep -oE 'PROJECT-[0-9]+' file.md | sort -u

# 2. Fetch metadata per ticket
acli jira workitem view PROJECT-1234 --json | jq '{
  status: .fields.status.name,
  assignee: .fields.assignee.displayName,
  priority: .fields.priority.name,
  labels: .fields.labels
}'

# 3. Find all tickets in an epic (any status)
acli jira workitem search --jql 'parent = PROJECT-1000' --json | jq -r '.[].key'

# 4. Check for tickets in Jira not in your markdown
acli jira workitem search --jql 'parent = PROJECT-1000 AND status = Backlog' --json | jq -r '.[].key'
```

### Extracting description links from ADF

Jira descriptions contain links in `inlineCard` or `link` mark format. To extract:

```bash
acli jira workitem view PROJECT-1234 --json | jq '.fields.description'
```

Search the nested ADF content recursively for `href` or `url` fields to find embedded links.

### Dependency ordering (topological sort)

To order tickets so dependencies appear before dependents:
1. From "Link work items → is blocked by" sections, build: `ticket → [list of blockers]`
2. Use Kahn's algorithm: process tickets with zero blockers first; decrement in-degree of dependents as each is processed.

## Common failure modes + fixes

- **Field not allowed / not found**: remove the field; retry; only use `'*all'` when needed.
- **Too much output**: prefer `--fields` with a minimal set.
- **Epic child query returns nothing**: try the alternative epic pattern (`parent =` vs `"Epic Link" =`), or remove status filters.
- **Moved tickets**: Jira may redirect keys (e.g., `OLD-5652 → NEW-2834`). Treat the redirected key as canonical in notes.
- **Large epics**: fetch comments only for non-Done tickets or tickets updated in the review window.
- **`workitem comment list` truncates ADF body**: the `comment list` command flattens comment text and may silently drop content. Use `workitem view --json --fields 'comment'` to get the full ADF structure, then extract `.fields.comment.comments[].body.content` for the real text.
