---
name: github
description: "Manages GitHub issues/PRs/repos using GitHub CLI (gh). Retrieve context, create/edit issues and PRs, manage workflows, and resolve review threads. Use when GitHub issues/PRs are mentioned, when you need details for planning, or when managing PR/issue workflows."
allowed-tools: "Bash(git:*), Bash(gh:*), Bash(jq:*), Read"
argument-hint: [issue-number or owner/repo#number]
user-invocable: false
---

# GitHub retrieval with `gh`

## Scope + defaults

- Default to **read-only** GitHub access. Do not create/edit/comment/close/merge or otherwise modify GitHub state unless explicitly requested.
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

### Issue write operations

**Create issue:**
```bash
gh issue create --title "<title>" --body "<body>"
gh issue create --title "<title>" --body "<body>" --label <label1>,<label2>
gh issue create --title "<title>" --body "<body>" --assignee <username>
```

**Edit issue:**
```bash
gh issue edit <ISSUE_NUMBER> --title "<new-title>"
gh issue edit <ISSUE_NUMBER> --body "<new-body>"
gh issue edit <ISSUE_NUMBER> --add-label <label1>,<label2>
gh issue edit <ISSUE_NUMBER> --add-assignee <user1>,<user2>
```

**Close issue:**
```bash
gh issue close <ISSUE_NUMBER>
gh issue close <ISSUE_NUMBER> --reason "completed"
```

**Add comment:**
```bash
gh issue comment <ISSUE_NUMBER> --body "<comment-text>"
```

## Actions & Workflows

### Manage workflows

**List workflows:**
```bash
gh workflow list
```

**Enable/disable workflows:**
```bash
gh workflow enable <workflow-file-name-or-id>
gh workflow disable <workflow-file-name-or-id>
```

**Trigger workflow manually:**
```bash
gh workflow run <workflow-file-name-or-id>
gh workflow run <workflow-file-name-or-id> -f <input-name>=<input-value>
```

### View and control runs

**List workflow runs:**
```bash
gh run list
gh run list --workflow <workflow-name-or-id>
gh run list --status failure
```

**Filter by commit:**
```bash
COMMIT_SHA=$(git rev-parse HEAD)
gh run list --head-sha $COMMIT_SHA
```

**View run details:**
```bash
gh run view <run-id>
gh run view <run-id> --json status,conclusion,createdAt,updatedAt,headBranch
```

**View logs:**
```bash
gh run view <run-id> --log
gh run view <run-id> --log-failed
gh run download <run-id> -D <output-dir>
```

**List jobs in run:**
```bash
gh run view <run-id> --json jobs --jq '.jobs[] | {name, status, conclusion}'

# Rerun failed run
gh run rerun <run-id>
gh run rerun <run-id> --failed

# Cancel run
gh run cancel <run-id>
```

### PR-specific workflow queries

```bash
# Get latest run for PR
PR=<PR_NUMBER>
COMMIT_SHA=$(gh pr view $PR --json commits -q '.commits[-1].oid')
gh run list --head-sha $COMMIT_SHA --limit 1 --json status,conclusion,name,createdAt,url

# Get latest run on main
gh run list --branch main --limit 1 --json status,conclusion,createdAt,workflowName
```

## Write operations (when explicitly requested)

- Any GitHub side effect requires explicit user approval.
- Never merge into the base branch via CLI; merges happen via the GitHub UI.

### Creating or editing a PR

Use **pull-request** for PR creation instructions. This skill covers only the CLI side.

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

### Resolving and unresolving review threads

Resolve a single thread:

```bash
gh api graphql -f id="<THREAD_ID>" -f query='
mutation($id: ID!) {
  resolveReviewThread(input: {threadId: $id}) {
    thread { id isResolved }
  }
}
'
```

Unresolve a thread:

```bash
gh api graphql -f id="<THREAD_ID>" -f query='
mutation($id: ID!) {
  unresolveReviewThread(input: {threadId: $id}) {
    thread { id isResolved }
  }
}
'
```

Batch resolve all threads on a PR:

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
PR=<PR_NUMBER>

gh api graphql -f o="$OWNER" -f r="$REPO" -f p="$PR" -f query='
query($o: String!, $r: String!, $p: Int!) {
  repository(owner: $o, name: $r) {
    pullRequest(number: $p) {
      reviewThreads(first: 100) {
        nodes { id }
      }
    }
  }
}
' -q '.data.repository.pullRequest.reviewThreads.nodes[].id' | while read id; do
  gh api graphql -f i="$id" -f query='
  mutation($i: ID!) {
    resolveReviewThread(input: {threadId: $i}) {
      thread { id isResolved }
    }
  }
  ' && echo "✅ $id"
done
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

## Troubleshooting

**Wrong repo**: Add `--repo <owner/repo>` explicitly.

**Not authenticated**: `gh auth status` → `gh auth login` (scopes: `repo`, `gist`, `read:org`). If `GITHUB_TOKEN` is invalid: `unset GITHUB_TOKEN GH_TOKEN`.

**Repository not found**: Either not in a git repo (`git rev-parse --git-dir`) or REST shorthand failing. Extract explicitly: `OWNER=$(gh repo view --json owner -q .owner.login)`, `REPO=$(gh repo view --json name -q .name)`.

**No push permission**: Check `gh repo view <owner/repo> --json viewerPermission`. If `READ` only, push to a fork: `gh pr create --repo upstream --base main --head user:branch`.

**Too much output**: Use `--json` with narrow field list.

**GraphQL variable error**: Declare in signature: `mutation($id: ID!) { ... }` not `mutation { ... }`.

**Debug**: `GH_DEBUG=api gh <command>` shows actual API calls.
