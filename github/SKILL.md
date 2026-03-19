---
name: github
description: Retrieves GitHub issue/PR/repo context using GitHub CLI (gh) in read-only mode. Use when GitHub issues/PRs are mentioned, when you need PR details/reviews/checks, or when you need a small list of issues/PRs for planning notes.
allowed-tools: "Bash(gh:*), Read, Grep, Glob"
---

# GitHub retrieval with `gh`

## Scope + defaults

- Default to **read-only** GitHub access.
- Do not create/edit/comment/close/merge or otherwise modify GitHub state unless explicitly requested.
- Prefer **small, targeted** reads (specific PR/issue, or a small list) over dumping large JSON.
- When writing notes, follow any workspace-specific link format from `CLAUDE.md` / `AGENTS.md`. Common format:
  - `[<repo>#<issue/pr number> <Issue/PR name shorten to 20 characters>](<url>)`

## Repo selection (critical)

- `gh` defaults to the **current git repository**.
- If the target is in another repo, always pass `--repo <owner/repo>`.

Examples:

```bash
gh pr view 12345 --repo owner/repo
gh issue view 678 --repo owner/other-repo
```

## Quick start (common reads)

### View a PR (human-readable)

```bash
gh pr view 12345 --repo owner/repo
```

### View a PR including comments + checks (JSON)

Prefer JSON for structured extraction (status, reviewers, checks):

```bash
gh pr view 12345 --repo owner/repo --json number,title,state,url,author,assignees,labels,baseRefName,headRefName,mergeable,reviewDecision,reviewRequests,reviews,commits,files,checks,statusCheckRollup
```

### PR inline review comments (diff comments)

Use this when you need the per-file / per-line review comments (often `discussion_r...`):

- Note: `gh pr view <num> --comments` is convenient but can truncate output. If you truly need **all** comments, prefer the `gh api ... --paginate` endpoints below (and consider `--jq` to keep output small).

```bash
gh api repos/owner/repo/pulls/12345/comments --paginate
```

PR "conversation" comments (non-diff) come from the issues endpoint:

```bash
gh api repos/owner/repo/issues/12345/comments --paginate
```

### View an issue (human-readable)

```bash
gh issue view 678 --repo owner/repo
```

### View an issue with comments (JSON)

```bash
gh issue view 678 --repo owner/repo --json number,title,state,url,author,assignees,labels,milestone,projects,body,comments
```

### List PRs (small sets)

```bash
gh pr list --repo owner/repo --state open --limit 20
```

Filtered variants:

```bash
gh pr list --repo owner/repo --search "author:@me is:open" --limit 20
gh pr list --repo owner/repo --search "review-requested:@me is:open" --limit 20
```

### List issues (small sets)

```bash
gh issue list --repo owner/repo --state open --limit 50
```

### Search code across the org (e.g. "is this file/pattern still used?")

Use `gh api search/code` to check whether a file, function, or variable is referenced anywhere in the org — useful before removing something.

```bash
# Check if a file is referenced anywhere in the org
gh api "search/code?q=filename.sh+org:myorg&per_page=100" \
  --jq '.total_count, (.items[] | {repo: .repository.full_name, path: .path, url: .html_url})'

# Check if a variable/function name is used
gh api "search/code?q=MY_VARIABLE+org:myorg&per_page=100" \
  --jq '.total_count, (.items[] | {repo: .repository.full_name, path: .path})'
```

- `total_count: 0` means nothing references it — safe to remove.
- Results include repo + file path so you can assess each hit before deleting.

## Extraction guidance (what to pull into notes)

When summarizing an issue/PR for a workspace, extract only what is needed:

- **What it is**: title + intent (1 sentence)
- **Status**: open/closed/merged/draft + review decision
- **Blockers**: failing checks, requested changes, missing approvals, dependency PRs/issues
- **Next action**: who needs to do what next (if clear)
- **Evidence links**: 1 canonical link in the workspace format (avoid link spam)

## Common failure modes + fixes

- **Wrong repo**: add `--repo <owner/repo>`.
- **Auth/permissions errors**: avoid write operations; if reads fail, note that access may be required or the user must authenticate locally (`gh auth status` can help diagnose).
- **No push permission to upstream repo**: if `gh repo view <owner/repo> --json viewerPermission` shows `READ`, you won't be able to `git push origin` (and `gh` can't create branches in the upstream repo). Push to a fork and open the PR from `fork:branch` to `upstream:base`.
- **GitHub HTML 404**: fetching GitHub PR/comment pages directly (e.g. via browser/WebFetch) can 404 without auth; prefer `gh` reads. For comment anchors: `#issuecomment-<id>` → `gh api repos/<owner>/<repo>/issues/comments/<id>`, inline PR review comment IDs → `gh api repos/<owner>/<repo>/pulls/comments/<id>`.
- **Too much output**: use `--json` with a narrow field list; avoid `--json '*all'` unless explicitly needed.
- **403 Forbidden / TLS errors (Claude Code sandbox)**: GitHub (`github.com`) is in the sandbox network allowlist, so `gh` commands (including `gh api` and `gh api graphql`) should work **without** `required_permissions`. Always try in sandbox first. Only escalate to `required_permissions: ["full_network"]` if the command actually fails with `403 Forbidden` or `tls: failed to verify certificate (x509 / OSStatus -26276)`. Do **not** preemptively request `full_network` for `gh` commands.

### Fork-first PR flow (when upstream is read-only)

1) Confirm permission:

```bash
gh repo view owner/repo --json viewerPermission
```

2) Add a fork remote and push:

```bash
git remote add fork git@github.com:<your-user>/repo.git
git push -u fork HEAD
```

3) Create the PR from the fork branch:

```bash
gh pr create --repo owner/repo --base main --head <your-user>:<branch>
```

### `gh` auth selection gotcha

- If `gh auth status` reports an **invalid `GITHUB_TOKEN`**, `gh` will prefer it over keychain/keyring auth. If you intend to use your saved login, run commands with:

```bash
unset GITHUB_TOKEN GH_TOKEN
```

## Write operations (when explicitly requested)

- **Approvals**: Any GitHub side effect (create/edit PRs, comments, reviews, labels, assignees, milestones, merges, releases) requires explicit user approval unless the user instructed otherwise.
- **Merges**: Never merge into the base branch via CLI; merges happen via the GitHub UI. Follow repository merge settings (squash/rebase/merge); do not enforce a merge strategy.

### Remove yourself as requested reviewer

This removes an explicit review request for your user (not team requests):

```bash
gh api repos/<owner>/<repo>/pulls/<n>/requested_reviewers --method DELETE --field 'reviewers[]=<your_login>'
```

Notes:
- Quote `reviewers[]=` (zsh treats `[]` as a glob).
- If this fails with permission/scope errors, try forcing non-CI auth: `env -u GITHUB_TOKEN -u GH_TOKEN gh api ...`.

### Unsubscribe / mute notifications for a PR

GitHub exposes per-issue/PR subscription state, but updating it can require the `notifications` scope.

#### Option A: per-issue subscription (may 404/403)

```bash
gh api repos/<owner>/<repo>/issues/<n>/subscription --method PUT --field ignored=true --field subscribed=false
```

If the REST endpoint returns 404/403 (common with limited tokens), prefer Option B (notifications thread) or use the GitHub UI
(right sidebar: Unsubscribe / Ignore).

#### Option B: ignore the notifications thread (works even when Option A fails)

1) Find the notification thread ID for a PR (note: adding params defaults to POST, so force `-X GET`):

```bash
PR_URL="$(gh api repos/<owner>/<repo>/pulls/<n> --jq .url)"
THREAD_ID="$(gh api -X GET notifications --paginate | jq -r --arg u "$PR_URL" '.[] | select(.subject.url == $u) | .id' | head -n 1)"
```

2) Ignore (mute) the thread:

```bash
gh api -X PATCH notifications/threads/$THREAD_ID -f ignored=true
```

If you get a scope error, refresh auth with notifications scope:

```bash
gh auth refresh -h github.com -s notifications
```

### Creating or editing a PR

- Use **create-pull-request** for all instructions related to creating a PR: template usage, title/body preferences, draft by default, issue linkage, test plan. This skill (github) covers only the CLI side.
- Commands: `gh pr create` (optionally `--draft`), `gh pr edit <number> --title "..." --body "..."`. Use `--repo <owner/repo>` when the PR is not in the current git repo.
- Do not add or modify repo `.github/*` templates unless the user explicitly asks.

**`gh pr create` when a PR already exists for the branch**: exits with code 1 ("a pull request for branch X already exists"). Use `gh pr edit <number>` to update the existing PR instead. You must also be on the correct branch — `gh pr create` resolves the branch from the current git checkout, so `git checkout <branch>` before running it.

**Converting a PR to draft**: `gh pr edit` does not have a `--draft` flag. Use:
```bash
gh pr ready <number> --undo
```

**Converting a draft PR to ready-for-review**:
```bash
gh pr ready <number>
```

### Posting reviews

**Approve:**
```bash
gh pr review <n> --repo <r> --approve --body "..."
```

**Request changes:**
```bash
gh pr review <n> --repo <r> --request-changes --body "..."
```

**Comment only (no verdict):**
```bash
gh pr review <n> --repo <r> --comment --body "..."
```

**Inline comments via REST API** (use when attaching per-line comments alongside a verdict):
```bash
gh api repos/<r>/pulls/<n>/reviews --method POST \
  --field commit_id="<head_sha>" \
  --field event="APPROVE" \        # or REQUEST_CHANGES or COMMENT
  --field body="<summary_body>" \
  --field "comments[][path]=<file>" \
  --field "comments[][line]=<line_number>" \
  --field "comments[][side]=RIGHT" \
  --field "comments[][body]=<comment_body>"
```

**Get head SHA** (required for inline comment API):
```bash
gh pr view <n> --repo <r> --json headRefOid --jq .headRefOid
```

**Resolve file line numbers** (required for inline comment positioning):
```bash
gh api "repos/<r>/contents/<path>?ref=<sha>" --jq '.content' | base64 -d | grep -n <pattern>
```
Escalate to `required_permissions: ["full_network"]` if this returns 403.

**Delete a review comment:**
```bash
gh api repos/<r>/pulls/comments/<id> --method DELETE
```
