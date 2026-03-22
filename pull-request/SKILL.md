---
name: pull-request
description: "Create and update pull requests as an author. Use when you're ready to propose changes: creates PRs with comprehensive file validation, tests, commit messages, and PR descriptions. Also guides addressing reviewer feedback through iterative fixes and comment resolution."
allowed-tools: "Bash(git:*), Bash(gh:*), Read, Edit, Write, Grep, Glob, AskUserQuestion"
argument-hint: [branch-name]
disable-model-invocation: true
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
3. **Validate & Fix**: Check artifacts/secrets, run pre-commit hooks
4. **Test & Document**: Run tests, update CHANGELOG/README/docstrings
5. **Commit & Push**: Create commit message, push to origin
6. **Create PR**: Push branch, create draft PR via gh-cli, clean up temp files

---

## Title Preferences

- **Short, scoped, action-oriented.** Prefer: `Scope: what the PR does`.
- Examples: `CLI: add retry flag for transient errors`, `Pipelines: add step for X`.
- Human-readable summary, not a raw Conventional Commit line.
- No ticket prefixes in the title unless the team convention requires it.

## Body Preferences

**For feature/fix PRs**: Short **bullet list**. One bullet per main change; concise phrasing.

**For refactoring/architectural PRs**: High-level **narrative format** (Problem → Solution → Impact) explaining why the changes matter. Include impact metrics or scope.

**Always include**:
- When the change has **measurable impact** (performance, reduced lines, security fixes): add a short **impact** block with before/after or what is skipped.
- **Issue ticket**: Include "Issue ticket number and link"; use N/A when there is no ticket.
- **Checklist**: Use `- [ ]` or `- [x]` per actual state; keep the template checklist and links at the bottom.

### Example PR body (feature/fix)

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
- [x] Tests pass locally
```

### Example PR body (refactoring/architectural)

```markdown
## Problem

[1-2 sentences: What's broken, confusing, or suboptimal]

## Solution

[How you're fixing it, organized by theme]

## Impact

[User/maintainer/operational benefits]

## Metrics

- [Before/after stats: lines, complexity, performance, security]
```

## CREATE Instructions

### Phase 1: Setup

**Always branch from the repo's default branch** (usually `main`) explicitly: `git checkout -b <branch> main`.

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

### Phase 2: File Selection

```bash
git status --porcelain
# Ask user: which files to stage?
# Offer categories: Modified | Untracked | All
```

Auto-exclude: `.gitignore` patterns, temp files, virtual envs, build artifacts

### Phase 3: Validate & Fix

**Check files**:
- ⚠️ No Claude artifacts (`.analysis`, `.claude`, `.report`, `.debug`)
- ⚠️ No temp files (`.tmp`, `.lock`, `.swp`, `~`, `.DS_Store`)
- ⚠️ No untracked files (should they be staged?)
- ⚠️ No secrets (password, api_key, token, credential fields)

**Run pre-commit fixes**:
```bash
git diff --cached | grep -iE '(password|secret|api[_-]?key|token|credential)["\s]*[:=]' && { exit 1; }
make pre-commit || make format  # Auto-fix linting/formatting
```

### Phase 4: Test & Document

**Run tests** (skip for docs-only changes):
```bash
STAGED=$(git diff --cached --name-only)
if echo "$STAGED" | grep -vqE '\.(md|txt)$'; then
  make test || { echo "❌ Tests failed"; exit 1; }
fi
```

**Update documentation** (if code changed):
- [ ] CHANGELOG.md (if repo uses one)
- [ ] README (for user-facing changes)
- [ ] Function docstrings

### Phase 5: Prepare Commit & PR

**Commit message** (summarizing changes):
```markdown
Brief summary from changed files

- Key change 1
- Key change 2

Co-Authored-By: Claude Code <noreply@anthropic.com>
```

**PR description** (from commit message + testing status):
```markdown
## Summary
[From commit message]

## Changes
[From git diff summary]

## Testing
- Tests: ✅ Passing
```

Save both to `COMMIT_MESSAGE.md` and `PR_DESCRIPTION.md`.

### Phase 6: Push & Create PR

**Before proceeding**: Confirm that you're ready to push to origin and create the PR. Review the commit message and PR body one more time if needed.

**Confirmation**: Ask the user: "Ready to push to origin and create PR? (yes/no)"

Only proceed if user explicitly confirms.

**Options**: Draft by default; use `--repo <owner/repo>` for non-current repo; use `Closes #X` in body for issue linkage.

**If confirmed:**

```bash
git commit -F COMMIT_MESSAGE.md
git push -u origin $FEATURE_BRANCH

gh pr create \
  --base main \
  --head $FEATURE_BRANCH \
  --draft \
  --title "<auto-generated-title>" \
  --body-file PR_DESCRIPTION.md

# Cleanup temp files
rm -f COMMIT_MESSAGE.md PR_DESCRIPTION.md
echo "✅ PR created"
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

### Phase 1: Auto-detect PR

```bash
PR=$(gh pr view --json number -q .number 2>/dev/null) || {
  echo "❌ No open PR for current branch"
  exit 1
}
echo "✅ Found PR #$PR"
```

### Phase 2: Fetch Comments

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
gh api repos/$OWNER/$REPO/pulls/$PR/comments \
  --jq '.[] | {id, path, line, body}' > /tmp/pr_comments.json
```

### Phase 3: Categorize Comments

Triage each comment as:
- **Must-fix**: Safety, correctness, required standards
- **Enhancement**: Improvements, consistency, best practices
- **NIT**: Formatting, cosmetic (can skip)

Summarize for user approval: "Fix X must-fixes and Y enhancements? (y/n)"

### Phase 4: Apply Fixes

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

### Phase 5: Verify Staged Files

Before committing, check:
- No Claude artifacts or temp files
- Only intended files are staged
- If uncertain, unstage and verify

### Phase 6: Security & Tests

Same checks as CREATE mode:
- Secrets check
- Pre-commit validation
- Tests (skip docs-only)
- Documentation validation

### Phase 7: Commit & Push

```bash
git commit -m "fix: address review feedback

- Addressed X comments
- Applied Y improvements"

git push origin $(git branch --show-current)
```

### Phase 8: Resolve Comments

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
