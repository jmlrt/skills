---
name: pull-request
description: Create and update pull requests, then iterate on review feedback. Covers PR templates, title/body conventions, file validation, and addressing reviewer comments.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, AskUserQuestion
disable-model-invocation: true
argument-hint: "[branch-name]"
---

# Pull Request Workflow (Author)

Create and update pull requests as an author: prepare PRs, push for review, then address reviewer feedback.

---

## Which Phase Are You In?

| Phase | Triggers | Details |
|-------|----------|---------|
| **CREATE** | "create a PR", "make a pull request", "open a PR", "submit for review" | [→ See CREATE section below](#create-mode-new-pr) |
| **ITERATE** | "address PR review", "fix PR feedback", "address review comments" | [→ See ITERATE section below](#iterate-mode-address-feedback) |

When your PR is ready to merge, reviewers use the **review-pull-request** skill to validate.

---

## Prerequisites

Before starting any mode, ensure:
- You're in a git repository
- GitHub CLI is installed and authenticated (`gh auth login`)
- You have write access to the repository

---

# CREATE Mode: New PR

Creates a new pull request with comprehensive safety checks.

## PR Template and Structure

- **If the repo has a pull request template** in `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/`, always use it.
- Use the template's section headings and checklist in the PR body. Fill in each section; keep any links (e.g. Contributing guide) at the bottom.
- **If there is no template**, still apply the title and body preferences below.
- Do not add or change the template file itself unless explicitly requested.

## Workflow

1. **Setup**: Fetch latest, rebase feature branch
2. **Files**: Select files to stage
3. **Validate**: File validation, secrets check
4. **Tests**: Run tests (docs-only changes skip this)
5. **Commit**: Create commit with auto-generated message
6. **Push & PR**: Push branch, create draft PR via gh-cli
7. **Cleanup**: Remove temp files

---

## Title Preferences

- **Short, scoped, action-oriented.** Prefer: `Scope: what the PR does`.
- Examples: `CLI: add retry flag for transient errors`, `Pipelines: add step for X`.
- Human-readable summary, not a raw Conventional Commit line.
- No ticket prefixes in the title unless the team convention requires it.

## Body Preferences

- **Describe your changes**: Short **bullet list**. One bullet per main change; concise phrasing.
- When the change has **measurable impact** (performance, which jobs/hooks run): add a short **impact** block with before/after or what is skipped. Use **lists and sub-bullets**, not tables.
- **Issue ticket**: Include "Issue ticket number and link"; use N/A when there is no ticket.
- **Checklist**: Use `- [ ]` or `- [x]` per actual state; keep the template checklist and links at the bottom.

### Example PR body structure

```markdown
## Describe your changes

- Extract dependency installation into setup script
- Reuse existing virtualenv when requirements unchanged

**Pre-commit duration impact:**
- **Before this PR:** ~49s total
- **After this PR:** ~12s total (90% faster)

## Issue ticket

Closes #123

## Checklist before requesting a review
- [ ] I have read the Contributing guide
- [x] Tests pass locally
```

## Additional Considerations

- **Create as draft by default** unless the user asks for ready-for-review.
- **Issue linkage**: Use `Closes #X` or `Addresses #X` in the body to link the PR to issues.
- **Repo selection**: Use `--repo <owner/repo>` when the PR is not in the current git repo.
- **Branch base**: Always branch from the repo's default base branch (usually `main`) explicitly — `git checkout -b <branch> main`.
- **Multiple PRs in one session**: `git checkout <branch>` into the correct branch before each `gh pr create` call.
- **Fork-first PR flow** (when upstream is read-only):
  ```bash
  gh repo view owner/repo --json viewerPermission
  git remote add fork git@github.com:<your-user>/repo.git
  git push -u fork HEAD
  gh pr create --repo owner/repo --base main --head <your-user>:<branch>
  ```

## CREATE Instructions

### Step 1: Setup

```bash
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)

# If on main/master, ask for feature branch name
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "Enter feature branch name:"
  # Read from user
else
  FEATURE_BRANCH=$CURRENT_BRANCH
fi

# Rebase on main
if ! git merge-base --is-ancestor origin/main HEAD; then
  GIT_EDITOR=true git rebase origin/main || {
    echo "❌ Rebase conflict. Resolve manually, retry."
    git rebase --abort
    exit 1
  }
fi
echo "✅ Up-to-date with main"
```

### Step 2: File Selection

```bash
git status --porcelain
# Ask user: which files to stage?
# Offer categories: Modified | Untracked | All
```

Auto-exclude: `.gitignore` patterns, temp files, virtual envs, build artifacts

### Step 3: File Validation

Before staging, verify:
- ⚠️ No Claude artifacts (`.analysis`, `.claude`, `.report`, `.debug`)
- ⚠️ No temp files (`.tmp`, `.lock`, `.swp`, `~`, `.DS_Store`)
- ⚠️ No untracked files (should they be staged?)
- ✅ Files are in-scope (same directory or related)

If uncertain, ask Claude to validate staged files.

### Step 4: Security & Pre-commit

```bash
# Check for secrets
git diff --cached | grep -iE '(password|secret|api[_-]?key|token|credential)["\s]*[:=]' && {
  echo "⚠️ Potential secrets detected. Fix before proceeding."
  exit 1
}

# Run pre-commit or make check
make pre-commit || {
  echo "Auto-fixing..."
  # Re-run after fixes
}
```

### Step 5: Tests

```bash
STAGED=$(git diff --cached --name-only)

# Skip tests for docs-only changes
if echo "$STAGED" | grep -vqE '\.(md|txt)$'; then
  make test || { echo "❌ Tests failed"; exit 1; }
else
  echo "⏭️ Docs-only, skipping tests"
fi
```

### Step 6: Documentation

If code changed (not just docs), ensure:
- [ ] CHANGELOG.md updated if the repo uses one
- [ ] README updated for user-facing changes
- [ ] Function docstrings added/updated

### Step 7: Commit

Generate commit message summarizing changes:

```markdown
Brief summary from changed files

- Key change 1
- Key change 2

Co-Authored-By: Claude Code <noreply@anthropic.com>
```

Stage in `COMMIT_MESSAGE.md`, commit with `git commit -F COMMIT_MESSAGE.md`

### Step 8: PR Description

Generate from commit message and changed files:

```markdown
## Summary
[From commit message]

## Changes
[From git diff summary]

## Testing
- Tests: ✅ Passing
- Coverage: X%
```

Save to `PR_DESCRIPTION.md`

### Step 9: Push and Create PR

```bash
git push -u origin $FEATURE_BRANCH

gh pr create \
  --base main \
  --head $FEATURE_BRANCH \
  --draft \
  --title "<auto-generated-title>" \
  --body-file PR_DESCRIPTION.md
```

### Step 10: Cleanup

```bash
rm -f COMMIT_MESSAGE.md PR_DESCRIPTION.md
echo "✅ PR created: https://github.com/..."
```

---

# ITERATE Mode: Address Feedback

Address review feedback on an existing PR.

## Workflow

1. **Auto-detect PR**: Find PR from current branch
2. **Fetch comments**: Get all review comments via GitHub API
3. **Categorize**: Sort as must-fix/enhancement/NIT
4. **Fix & validate**: Apply fixes, run tests, scan for similar patterns
5. **Commit & resolve**: Commit fixes, mark comments resolved
6. **Summary**: Show what was done

---

## ITERATE Instructions

### Step 1: Auto-detect PR

```bash
PR=$(gh pr view --json number -q .number 2>/dev/null) || {
  echo "❌ No open PR for current branch"
  exit 1
}
echo "✅ Found PR #$PR"
```

### Step 2: Fetch Comments

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
gh api repos/$OWNER/$REPO/pulls/$PR/comments \
  --jq '.[] | {id, path, line, body}' > /tmp/pr_comments.json
```

### Step 3: Categorize Comments

Triage each comment as:
- **Must-fix**: Safety, correctness, required standards
- **Enhancement**: Improvements, consistency, best practices
- **NIT**: Formatting, cosmetic (can skip)

Summarize for user approval: "Fix X must-fixes and Y enhancements? (y/n)"

### Step 4: Apply Fixes

For each must-fix and enhancement:
1. Read affected file (use Read tool)
2. Apply fix based on comment
3. Stage file: `git add <file>`

**After each fix:**
- Re-read the changed block to confirm correctness
- **Proactively scan the codebase for the same pattern** — don't wait for next review cycle
- Fix all occurrences found in the codebase

Common grep patterns:
```bash
# Broad exception handlers
grep -rn "except Exception:" src/

# Missing validation
grep -rn "\.exists()" src/ | grep -v "is_dir"

# Hardcoded values
grep -rn "if.*> [0-9]\|== ['\"]" src/ | grep -v "test"
```

**Safety checks during fixes:**
- **CLAUDE.md/settings**: Flag if the PR modifies `CLAUDE.md`, `settings.json`, or permission files — treat as critical
- **Cross-codebase patterns**: If you flag a pattern, grep for same pattern elsewhere and fix all occurrences

### Step 5: Verify Staged Files

Before committing, check:
- No Claude artifacts or temp files
- Only intended files are staged
- If uncertain, unstage and verify

### Step 6: Security & Tests

Same checks as CREATE mode:
- Secrets check
- Pre-commit validation
- Tests (skip docs-only)
- Documentation validation

### Step 7: Commit & Push

```bash
git commit -m "fix: address review feedback

- Addressed X comments
- Applied Y improvements"

git push origin $(git branch --show-current)
```

### Step 8: Resolve Comments

After fixes are pushed, mark comments as resolved:

```bash
# For each fixed comment
THREAD_ID=<thread-id>
gh api graphql -f id="$THREAD_ID" -f query='
mutation($id: ID!) {
  resolveReviewThread(input: {threadId: $id}) {
    thread { id isResolved }
  }
}
'

echo "✅ Comment resolved"
```

Batch resolve all threads using the github skill's batch resolve command.

---

## Next: Request Review

Once your fixes are pushed and comments resolved, request review from a maintainer. They'll use the **review-pull-request** skill to validate merge readiness.
