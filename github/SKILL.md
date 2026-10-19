---
name: github
description: "Non-obvious GitHub CLI (gh) mechanics: PR review comments and threads, posting reviews, merge queues, batched GraphQL mutations, and gh/jq gotchas. Use when working with the gh CLI or GitHub API."
allowed-tools: "Bash(git:*), Bash(gh:*), Bash(jq:*), Read"
argument-hint: [issue-number or owner/repo#number]
user-invocable: false
disable-model-invocation: false
---

# GitHub CLI (`gh`) mechanics

## Defaults

- Read-only by default. Any GitHub side effect (create, edit, comment, review, close, merge, label) needs explicit user approval for that action.
- Never merge into the base branch via CLI unless explicitly asked.
- `gh` targets the **current git repository**. For any other repo, always pass `--repo <owner/repo>`.
- Keep reads narrow: `--json` with a short field list, explicit `--method GET` for `gh api` reads.
- After any write, verify by re-querying GitHub; some failures are silent (exit 0, nothing done).

## Load a skill from a pull request

When a referenced skill only exists on an unmerged PR, fetch it and follow it as local guidance:

```bash
gh api "repos/<o>/<r>/contents/<path>/SKILL.md?ref=refs/pull/<N>/head" --jq '.content' | base64 --decode  # macOS: -D
```

`gh pr diff <N> --repo <o>/<r>` shows every new file at once.

## PR comments and history

- `gh pr view --comments` can truncate. Inline diff comments: `gh api --method GET repos/<o>/<r>/pulls/<N>/comments --paginate`. Conversation comments: `.../issues/<N>/comments`.
- Event history (merge queue, labels, force pushes) uses the **issues** endpoint; `pulls/<N>/timeline` returns 404:

```bash
gh api --method GET repos/<o>/<r>/issues/<N>/events --jq '.[] | .event + " " + .created_at + " " + .actor.login'
```

Useful events: `added_to_merge_queue`, `removed_from_merge_queue`, `labeled`, `head_ref_force_pushed`.

- `gh search prs --review-requested <user>` also matches team requests. Direct requests are in `requested_reviewers` of `repos/<o>/<r>/pulls/<N>`.
- `reviewDecision` is not available in `gh search prs --json`; use `gh pr view <N> --json reviewDecision`.

## Merge queue

`gh pr merge --auto` (and often `--squash`) does not reliably enqueue on merge-queue repos. Use GraphQL:

```bash
# 1. enqueuePullRequest fails while required checks are pending: wait first
gh pr checks <N> --repo <o>/<r> --watch
# 2. Node ID, then enqueue (mutation is enqueuePullRequest, not addPullRequestToMergeQueue)
PR_ID=$(gh api repos/<o>/<r>/pulls/<N> --jq '.node_id')
gh api graphql -f id="$PR_ID" -f query='mutation($id: ID!) { enqueuePullRequest(input: {pullRequestId: $id}) { mergeQueueEntry { position } } }'
```

To merge once checks pass instead, use `enablePullRequestAutoMerge(input: {pullRequestId: $id, mergeMethod: SQUASH})`. Verify either way:

```bash
gh api graphql -f query='{ repository(owner:"<o>", name:"<r>") { pullRequest(number:<N>) { mergeQueueEntry { position } autoMergeRequest { enabledAt } } } }' --jq '.data.repository.pullRequest'
```

Both null means nothing happened.

## Review threads

Resolving is GraphQL-only and needs thread IDs (`PRRT_...` from `reviewThreads`), not comment IDs (`PRRC_...`):

```bash
gh api graphql -f o=<o> -f r=<r> -F p=<N> -f query='
query($o: String!, $r: String!, $p: Int!) {
  repository(owner: $o, name: $r) { pullRequest(number: $p) {
    reviewThreads(first: 100) { nodes { id isResolved path comments(first: 1) { nodes { body } } } }
  } }
}'

gh api graphql -f id=<PRRT_ID> -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }'
```

Use `unresolveReviewThread` the same way. If GraphQL is unavailable, ask the user to resolve in the UI.

## Posting reviews

Simple reviews: `gh pr review <N> --repo <o>/<r> --approve|--request-changes|--comment --body-file <file>`.

Review with inline comments in one call (pin to the current head SHA):

```bash
SHA=$(gh pr view <N> --repo <o>/<r> --json headRefOid --jq .headRefOid)
gh api repos/<o>/<r>/pulls/<N>/reviews --method POST \
  -f commit_id="$SHA" -f event=COMMENT -F body=@summary.md \
  -f "comments[][path]=<file>" -F "comments[][line]=<line>" \
  -f "comments[][side]=RIGHT" -f "comments[][body]=<comment>"
```

`event` is `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`. Reply to a comment with `-F in_reply_to=<id>` on `pulls/<N>/comments`.

To change a posted comment, edit it rather than posting a correction: `gh api --method PATCH repos/<o>/<r>/issues/comments/<id> -F body=@file` (`<id>` from the `#issuecomment-<id>` fragment).

## Batching GraphQL mutations

Many writes in a loop are slow and can fail silently. Batch them as aliased mutations in one call, about 16 per call; split further on `RESOURCE_LIMITS_EXCEEDED`:

```bash
gh api graphql -f query='{ repository(owner:"<o>", name:"<r>") { id label(name:"<label>") { id } } }'

gh api graphql -f query='
mutation {
  a1: addLabelsToLabelable(input: {labelableId: "<NODE_ID_1>", labelIds: ["<LABEL_ID>"]}) { clientMutationId }
  a2: addLabelsToLabelable(input: {labelableId: "<NODE_ID_2>", labelIds: ["<LABEL_ID>"]}) { clientMutationId }
}' --jq '.data | keys[]'
```

The same pattern works for `createPullRequest`, `resolveReviewThread`, and other mutations. Re-query afterward to confirm every item.

## Troubleshooting

- **`--jq` object construction** (`--jq '{a: .x}'`) can silently return nothing. Use string concatenation or pipe to `jq`.
- **`--jq` only exists on `gh api`**, and rejects jq flags like `--arg`; pipe to `jq` instead.
- **`gh issue view --comments` and `--json` are mutually exclusive**: use `--json comments`.
- **`-f` sends strings, `-F` sends typed values** (numbers, booleans, `@file`). An `Int!` variable given with `-f` fails with "invalid value".
- **GraphQL variables** must be declared in the signature: `mutation($id: ID!) { ... }`.
- **GraphQL query**: pass with `-f query='...'`, not a heredoc on stdin.
- **Bodies with backticks or newlines**: write to a file, use `-F body=@file` or `--body-file`. A body starting with `@user` given via `-F` is read as a path; use `-f body="$BODY"`.
- **Quote URLs containing `?`** (zsh globbing).
- **`gh pr diff`** takes no file paths; use `--name-only` or the `pulls/<N>/files --paginate` API. If it returns empty, use the files API.
- **Empty `gh issue view` output**: fall back to `gh api repos/<o>/<r>/issues/<N>`.
- **GraphQL 502 or HTML responses**: switch to REST for the rest of the session instead of retrying.
- **PR head SHA can lag** after a push; check `git/refs` for `refs/heads/<branch>`.
- **Sub-issues endpoint** is `issues/<N>/sub_issues` (underscore).
- **`gh project item-list`** truncates silently; pass `--limit 1000`.
- **Reopening a PR after its branch was force-pushed** fails; open a new PR referencing the old one.
- **`gh pr create` on a branch that already has a PR** exits 1; use `gh pr edit`.
- **Parallel calls**: include the PR/issue number in each output line; completion order is random.
- **Debug**: `GH_DEBUG=api gh <command>` shows the API calls.
