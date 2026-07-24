---
name: github
description: "GitHub CLI (gh) mechanics: retrieving issues/PRs, posting reviews, managing workflow runs, and troubleshooting. Use when working with the gh CLI itself."
allowed-tools: "Bash(git:*), Bash(gh:*), Bash(jq:*), Read"
argument-hint: [issue-number or owner/repo#number]
user-invocable: false
disable-model-invocation: true
---

# GitHub CLI (`gh`) mechanics

## Scope + defaults

- Default to **read-only** GitHub access. Do not create/edit/comment/close/merge or otherwise modify GitHub state unless explicitly requested.
- Prefer **small, targeted** reads (specific PR/issue, or a small list) over dumping large JSON.
- Use explicit `--method GET` for `gh api` reads.
- Shell, sandbox, and authentication behavior varies by environment. Verify a failing command with `gh <command> --help` or the current GitHub CLI documentation before treating a workaround as universal.

### Load a skill from a pull request

When a referenced skill is only available on an unmerged PR branch, fetch its entry point directly and follow it as local guidance:

```bash
gh api repos/<owner>/<repo>/contents/<path-to-SKILL.md> --jq '.content' | base64 --decode
# macOS: replace --decode with -D
```

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
gh api --method GET repos/owner/repo/pulls/12345/comments --paginate
```

PR "conversation" comments (non-diff) come from the issues endpoint:

```bash
gh api --method GET repos/owner/repo/issues/12345/comments --paginate
```

### PR event history (merge queue, labels, assignments)

Use the **issues** events endpoint — the pulls timeline endpoint (`pulls/{n}/timeline`) returns 404:

```bash
gh api --method GET repos/owner/repo/issues/1598/events --jq '.[] | {event, created_at, actor: .actor.login}'
```

Useful events: `added_to_merge_queue`, `removed_from_merge_queue`, `labeled`, `head_ref_force_pushed`.

### Merge queue operations

**Adding a PR to the merge queue** requires GraphQL — `gh pr merge --auto` prints a message but does not enqueue when the repo uses a merge queue strategy:

```bash
# 1. Wait for required checks to pass (enqueuePullRequest fails if any are pending)
gh pr checks <number> --repo owner/repo --watch

# 2. Get the PR node ID
PR_ID=$(gh api graphql -f query='query { repository(owner:"<owner>", name:"<repo>") { pullRequest(number: <N>) { id } } }' --jq '.data.repository.pullRequest.id')

# 3. Enqueue
gh api graphql -f pullRequestId="$PR_ID" -f query='mutation($pullRequestId: ID!) { enqueuePullRequest(input: {pullRequestId: $pullRequestId}) { mergeQueueEntry { position } } }'
```

**Mutation name**: `enqueuePullRequest` — NOT `addPullRequestToMergeQueue` (that field does not exist).

**Alternative: auto-merge** — when checks haven't passed yet (so `enqueuePullRequest` would fail), use `enablePullRequestAutoMerge` to schedule merge-on-green instead of direct queue entry:

```bash
NODE_ID=$(gh api repos/<owner>/<repo>/pulls/<N> --jq '.node_id')
gh api graphql -f query="mutation { enablePullRequestAutoMerge(input: {pullRequestId: \"$NODE_ID\", mergeMethod: SQUASH}) { pullRequest { number autoMergeRequest { enabledAt } } } }"
```

**`gh pr merge --squash` unreliable on merge-queue repos**: returns `invalid character '{'` even when it works (PR silently enters queue) or silently does nothing. Always verify afterward: `gh api graphql -f query='{ repository(owner:"<org>",name:"<repo>") { pullRequest(number:<N>) { mergeQueueEntry { position } autoMergeRequest { enabledAt } } } }' --jq '.data.repository.pullRequest'`. If both are null, the command failed — use `enqueuePullRequest` or `enablePullRequestAutoMerge`.

### View an issue (JSON)

```bash
gh issue view 678 --repo owner/repo --json number,title,state,url,author,assignees,labels,milestone,projects,body,comments
```

### Compare two branches/commits

To check whether two branches have diverged (e.g. before assuming a pipeline/repo's `main` and a release branch run identical code), use the compare endpoint rather than manually diffing files:

```bash
gh api repos/owner/repo/compare/main...9.5 --jq '{status, ahead_by, behind_by}'
gh api repos/owner/repo/compare/main...9.5 --jq '.commits[] | {sha: .sha[0:8], message: (.commit.message | split("\n")[0])}'
gh api repos/owner/repo/commits/<sha> --jq '.files[] | {filename, patch}'   # see what a specific commit changed
```

`ahead_by`/`behind_by` > 0 means real divergence — worth checking before assuming behavior is identical across branches just because params/env look the same.

### List PRs

```bash
gh pr list --repo owner/repo --state open --limit 20
gh pr list --repo owner/repo --search "author:@me is:open" --limit 20
gh pr list --repo owner/repo --search "review-requested:@me is:open" --limit 20
```

**Draft PRs are not reliably included in `--state=all` or cross-repo searches.** When completeness matters (e.g. auditing all authored PRs), run a separate explicit `is:draft` search in addition to the main query:

```bash
gh api graphql -f query='{ search(query: "author:USERNAME is:pr is:draft created:>=YYYY-MM-DD org:ORG", type: ISSUE, first: 50) { nodes { ... on PullRequest { number title repository { nameWithOwner } } } } }'
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

**Edit existing comment** (when asked to modify a comment, always edit the existing one instead of adding a new one):
```bash
gh api repos/<owner>/<repo>/issues/comments/<COMMENT_ID> --method PATCH --input /dev/stdin <<'EOF'
{
  "body": "<updated-comment-text>"
}
EOF
```

**Cross-repo references in markdown** (for clickable links in comments, use full `owner/repo#number` format; omit owner only for local repo refs):
```markdown
owner/repo#123                  # Clickable cross-repo PR reference (requires owner/repo for cross-repo)
#1022                           # Local issue reference (current repo — owner optional)
```
**Note:** GitHub markdown auto-links `owner/repo#number` format; partial `repo#number` (without owner) is not clickable across repos. Always use the full format for cross-repo references.

**Links in issue/PR bodies and comments: bare URL or `owner/repo#number`, never `[text](url)` markdown link syntax.** GitHub auto-linkifies both. The `[text](url)` convention used for internal Notes/PKM workspace files does not apply here — that's for referencing GitHub items *from* markdown notes, not for content actually posted *to* GitHub.

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

**Backticks in `--body` heredocs**: do not escape backticks with `\`` in `--body "$(cat <<'EOF'...EOF)"` content. The single-quoted heredoc prevents all shell expansion — raw backticks are safe. Using `\`` causes the backslash to appear literally in the rendered GitHub description.

**Creating multiple PRs in bulk**: `gh pr create` (and `gh api` REST POST) fail with TLS keychain errors when called in a loop on macOS. Use a single batched `createPullRequest` GraphQL mutation instead:

```bash
# Get repo node ID first
gh api graphql -f query='{ repository(owner: "OWNER", name: "REPO") { id } }' \
  --jq '.data.repository.id'

# Create up to ~15 PRs in one call (resource limit ~16 mutations per call)
gh api graphql -f query='
mutation {
  pr1: createPullRequest(input: {
    repositoryId: "<REPO_ID>",
    title: "[8.19] <title> (#N)", baseRefName: "8.19", headRefName: "backport/8.19/pr-N",
    body: "Backport of #N.", draft: true
  }) { pullRequest { number url } }
  pr2: createPullRequest(input: {
    repositoryId: "<REPO_ID>",
    title: "[9.3] <title> (#N)", baseRefName: "9.3", headRefName: "backport/9.3/pr-N",
    body: "Backport of #N.", draft: true
  }) { pullRequest { number url } }
}' --jq '.data | to_entries[] | "\(.key): #\(.value.pullRequest.number) \(.value.pullRequest.url)"'
```

**Bulk labeling**: use `addLabelsToLabelable` mutations batched similarly. Get label ID: `gh api graphql -f query='{ repository(owner: "o", name: "r") { label(name: "backport") { id } } }' --jq '.data.repository.label.id'`. Batch at ~16 per call; split into a second call if you hit `RESOURCE_LIMITS_EXCEEDED`.

**Draft ↔ ready-for-review**:
```bash
gh pr ready <number> --undo   # → draft
gh pr ready <number>           # → ready
```

**Reopening a closed PR after a force push**: Both `gh pr reopen` and `PATCH state=open` will fail with "state cannot be changed. The branch was force-pushed or recreated." There is no workaround — create a new PR from the same branch instead (`gh pr create`), reference the old PR number in the body for context.

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

gh api graphql -f o="$OWNER" -f r="$REPO" --field p=$PR -f query='
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

**GraphQL Int! variable**: `-f p="$PR"` sends a string and fails with "Variable $p of type Int! was provided invalid value". Use `--field p=$PR` (no quotes) to send an integer.

**Review thread ID format**: `resolveReviewThread` requires thread IDs with `PRRT_...` prefix (from the `reviewThreads` query). Review comment IDs (`PRRC_...`) will fail with "Could not resolve to a node". Always fetch thread IDs via `reviewThreads(first: N) { nodes { id } }` before resolving.

**`gh api --jq` object construction silently returns empty**: never use `--jq '{key: .value}'` object construction syntax — it fails silently with no error. Use string concatenation instead (`'.f1 + " " + .f2'`) or pipe to `jq -r`:
```bash
# ❌ WRONG — silently returns empty
gh api repos/owner/repo/pulls/1 --jq '{state: .state, title: .title}'

# ✅ CORRECT — string concat
gh api repos/owner/repo/pulls/1 --jq '.state + " " + .title'

# ✅ CORRECT — pipe to jq
gh api repos/owner/repo/pulls/1 | jq -r '.state + " " + .title'
```

**`gh api` / `gh pr create` TLS failures on macOS**: two distinct failure modes:
- *Spawned scripts*: `gh api` in a child process (`bash script.sh`, `$()` in a loop) fails with `tls: failed to verify certificate: x509: OSStatus -26276`. Run `gh api` as direct inline Bash calls only.
- *Sequential calls in the same session*: even in a direct Bash tool invocation, calling `gh api` or `gh pr create` multiple times sequentially (e.g. in a shell loop) causes TLS failures on the second and subsequent calls. **The failure is silent — exit code is 0, any following `echo` runs, but the operation was never performed.** Always verify by querying GitHub after bulk write operations before assuming success.
- *Workaround for bulk writes*: use a single batched GraphQL mutation call (e.g. multiple aliased `createPullRequest` mutations) — one HTTPS connection, no sequential reconnects.

**GraphQL failure fallback**: if `gh api graphql` returns a 502, HTML, or TLS error, use the REST API instead:
```bash
gh api --method GET repos/<org>/<repo>/pulls/<N> --jq '{state, title, merged_at}'
# list all open PRs
gh api --method GET 'repos/<org>/<repo>/pulls?state=open' --jq '.[] | {number, state, title}'
# list closed/merged
gh api --method GET 'repos/<org>/<repo>/pulls?state=closed' --jq '.[] | {number, state, title, merged_at}'
```
Note: quote the URL when it contains `?` to prevent zsh glob expansion.

**`gh pr diff` does not support file path filtering**: `gh pr diff <N>` accepts only one positional arg (the PR number) — passing extra file paths fails with "accepts at most 1 arg(s)". To filter by filename, pipe through grep:
```bash
gh pr diff <N> --repo <owner>/<repo> | grep "^diff --git\|^+\|^-" | grep -A20 "filename-pattern"
# or to see only changed filenames:
gh pr diff <N> --repo <owner>/<repo> --name-only
```

**`gh pr diff` returns empty output**: TLS issues or large diffs can cause `gh pr diff` to silently return nothing. Fall back to the files API:
```bash
gh api --method GET repos/<owner>/<repo>/pulls/<number>/files --paginate \
  --jq '.[] | {filename, additions, deletions, patch}'
```

**Debug**: `GH_DEBUG=api gh <command>` shows actual API calls.

## Gists

**Secret vs public**: `gh gist create` creates a **secret** gist by default. Use `--public` for a public gist. There is **no `--secret` flag** — it will fail with "unknown flag: --secret".

```bash
gh gist create file1 file2           # secret (default)
gh gist create file1 file2 --public  # public
gh gist delete <gist-id>
gh gist edit <gist-id> -f filename /path/to/replacement-file
```

Gist revisions cannot be deleted via the API or UI — the only way to remove a revision is to delete the gist entirely and recreate it.
