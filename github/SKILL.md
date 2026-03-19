---
name: github
description: Retrieves GitHub issue/PR/repo context using GitHub CLI (gh) in read-only mode. Use when GitHub issues/PRs are mentioned, when you need PR details/reviews/checks, or when you need a small list of issues/PRs for planning notes.
allowed-tools: "Bash(gh:*), Read"
---

# GitHub retrieval with `gh`

## Prerequisites

- **gh CLI**: https://github.com/cli/cli

```bash
which gh || echo "gh not installed: https://github.com/cli/cli"
```

## Scope + defaults

- Default to **read-only** GitHub access.
- Do not create/edit/comment/close/merge or otherwise modify GitHub state unless explicitly requested.
- Prefer **small, targeted** reads (specific PR/issue, or a small list) over dumping large JSON.

## Repo selection (critical)

- `gh` defaults to the **current git repository**.
- If the target is in another repo, always pass `--repo <owner/repo>`.

## Quick start (common reads)

### View a PR (JSON)

```bash
gh pr view 12345 --repo owner/repo --json number,title,state,url,author,assignees,labels,baseRefName,headRefName,mergeable,reviewDecision,reviewRequests,reviews,commits,files,checks,statusCheckRollup
```

### PR inline review comments (diff comments)

- `gh pr view <num> --comments` is convenient but can truncate. For **all** comments, prefer `gh api` with `--paginate`:

```bash
gh api repos/owner/repo/pulls/12345/comments --paginate
```

PR "conversation" comments (non-diff) come from the issues endpoint:

```bash
gh api repos/owner/repo/issues/12345/comments --paginate
```

### View an issue (JSON)

```bash
gh issue view 678 --repo owner/repo --json number,title,state,url,author,assignees,labels,milestone,projects,body,comments
```

### List PRs

```bash
gh pr list --repo owner/repo --state open --limit 20
gh pr list --repo owner/repo --search "author:@me is:open" --limit 20
gh pr list --repo owner/repo --search "review-requested:@me is:open" --limit 20
```

### List issues

```bash
gh issue list --repo owner/repo --state open --limit 50
```

## Common failure modes + fixes

- **Wrong repo**: add `--repo <owner/repo>`.
- **Auth/permissions errors**: avoid write operations; if reads fail, check `gh auth status`.
- **No push permission to upstream repo**: if `gh repo view <owner/repo> --json viewerPermission` shows `READ`, push to a fork and open the PR from `fork:branch` to `upstream:base`.
- **Too much output**: use `--json` with a narrow field list.
- **403 Forbidden / TLS errors (Claude Code sandbox)**: `gh` commands should work without `required_permissions`. Try in sandbox first; only escalate to `required_permissions: ["full_network"]` if the command actually fails.

### Fork-first PR flow (when upstream is read-only)

```bash
gh repo view owner/repo --json viewerPermission
git remote add fork git@github.com:<your-user>/repo.git
git push -u fork HEAD
gh pr create --repo owner/repo --base main --head <your-user>:<branch>
```

### `gh` auth selection gotcha

If `gh auth status` reports an invalid `GITHUB_TOKEN`, `gh` prefers it over keychain auth. Fix with:

```bash
unset GITHUB_TOKEN GH_TOKEN
```

## Write operations (when explicitly requested)

- Any GitHub side effect requires explicit user approval.
- Never merge into the base branch via CLI; merges happen via the GitHub UI.

### Creating or editing a PR

Use **create-pull-request** for PR creation instructions. This skill covers only the CLI side.

```bash
gh pr create          # optionally --draft
gh pr edit <number> --title "..." --body "..."
```

**PR already exists for the branch**: `gh pr create` exits with code 1. Use `gh pr edit <number>` instead.

**Draft ↔ ready-for-review**:
```bash
gh pr ready <number> --undo   # → draft
gh pr ready <number>           # → ready
```

### Resolving review threads

```bash
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) { thread { isResolved } } }'
```

### Posting reviews

```bash
gh pr review <n> --repo <r> --approve --body "..."
gh pr review <n> --repo <r> --request-changes --body "..."
gh pr review <n> --repo <r> --comment --body "..."
```

**Inline comments via REST API**:
```bash
gh api repos/<r>/pulls/<n>/reviews --method POST \
  --field commit_id="<head_sha>" \
  --field event="APPROVE" \
  --field body="<summary_body>" \
  --field "comments[][path]=<file>" \
  --field "comments[][line]=<line_number>" \
  --field "comments[][side]=RIGHT" \
  --field "comments[][body]=<comment_body>"
```

**Get head SHA**:
```bash
gh pr view <n> --repo <r> --json headRefOid --jq .headRefOid
```
