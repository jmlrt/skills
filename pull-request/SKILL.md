---
name: pull-request
description: Guide pull requests through their complete lifecycle. Create new PRs, iterate on review feedback, and validate before merge. Covers PR template usage, title/body preferences, file validation, security checks, and merge readiness.
---

# Pull Request Lifecycle

Guide pull requests through their complete lifecycle: creation, feedback iteration, and merge validation.

---

## Which Phase Are You In?

| Phase | Triggers | Details |
|-------|----------|---------|
| **CREATE** | "create a PR", "make a pull request", "open a PR", "submit for review" | [→ See CREATE section below](#create-mode-new-pr) |
| **ITERATE** | "address PR review", "fix PR feedback", "address review comments" | [→ See ITERATE section below](#iterate-mode-address-feedback) |
| **VALIDATE** | "check if ready to merge", "pre-merge validation", "final PR check" | [→ See VALIDATE section below](#validate-mode-pre-merge-checks) |

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

Apply validation logic from Shared Validation Patterns section below:
- Flag Claude artifacts, temp files
- Warn about untracked files, out-of-scope files
- Require final confirmation

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

### Step 6: Documentation Validation

From Shared Validation Patterns: Warn if code changed but CHANGELOG.md missing

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

### Step 5: Validate Staged Files

Apply validation logic from Shared Validation Patterns section below:
- Flag Claude artifacts, temp files
- Warn about untracked files
- Require final confirmation

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

# VALIDATE Mode: Pre-Merge Checks

Final pre-merge validation to ensure PR is ready.

## Workflow

1. **Check PR status**: All required checks passing?
2. **Review comments resolved**: Any unresolved comments?
3. **Documentation**: CHANGELOG, README, docstrings updated?
4. **Coverage**: Tests coverage maintained?
5. **Consistency**: Code style, naming, patterns match?

---

## VALIDATE Instructions

### Step 1: PR Status

```bash
PR=$(gh pr view --json number -q .number)
gh pr view $PR --json statusCheckRollup -q '.statusCheckRollup[] | {name, status}'

# All must be "PASS" (not FAIL, PENDING, SKIPPED)
```

### Step 2: Review Status

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)

# Check for unresolved comments
gh api repos/$OWNER/$REPO/pulls/$PR/comments \
  --jq '.[] | select(.in_reply_to_id == null) | {path, line, body}'

# Count unresolved review threads
gh pr view $PR --json comments -q '.comments[] | select(.isResolved == false)' | wc -l
```

If unresolved comments exist: **STOP** — ask author to address

### Step 3: Documentation

Check that code changes have accompanying documentation:
- [ ] CHANGELOG.md updated with accurate description
- [ ] README.md updated if user-facing changes
- [ ] Docstrings added/updated for new functions
- [ ] Help text accurate (CLI/config)
- [ ] No misleading wording or overclaims

### Step 4: Coverage

```bash
# Verify tests pass and coverage maintained
make check

# If coverage dropped below threshold: STOP — ask for more tests
```

### Step 5: Consistency

Verify:
- Type hints present on public functions
- Naming conventions consistent (snake_case for Python, etc.)
- Error messages consistent format
- Patterns match existing codebase
- No hardcoded values (use constants)
- Exception handling specific (not broad `except Exception`)

### Step 6: Merge Decision

✅ **Ready to merge** if:
- All checks passing
- No unresolved review comments
- Documentation complete
- Coverage maintained
- Code consistency verified

❌ **Not ready** if anything above fails — ask for fixes

---

# Shared Validation Patterns

Reusable validation logic used across CREATE and ITERATE modes.

## File Validation

Applied before committing in both CREATE and ITERATE modes.

```bash
STAGED=$(git diff --cached --name-only)
UNTRACKED=$(git ls-files --others --exclude-standard)

# 1. Detect Claude/Analysis artifacts
SUSPICIOUS=$(echo "$STAGED" | grep -E '\.(analysis|claude|report|debug|txt\.bak)$|\.claude.*|.*\.analysis\..*' || true)
if [ ! -z "$SUSPICIOUS" ]; then
  echo "⚠️ Claude artifacts detected: unstage? (y/n)"
fi

# 2. Detect temp/lock files
TEMP=$(echo "$STAGED" | grep -E '\.tmp$|\.lock$|\.swp$|~$|\.DS_Store$' || true)
if [ ! -z "$TEMP" ]; then
  echo "⚠️ Temp files detected: unstage? (y/n)"
fi

# 3. Warn about untracked files
if [ ! -z "$UNTRACKED" ]; then
  echo "ℹ️ Untracked files exist: OK to skip? (y/n)"
fi

# 4. Check for out-of-scope files
FIRST_FILE=$(echo "$STAGED" | head -1)
SCOPE=$(echo "$FIRST_FILE" | xargs dirname)
OUT_OF_SCOPE=$(echo "$STAGED" | grep -v "^$SCOPE" | grep -v "CHANGELOG\|README\|\.github" || true)
if [ ! -z "$OUT_OF_SCOPE" ]; then
  echo "ℹ️ Out-of-scope files detected: OK? (y/n)"
fi

# 5. Final confirmation
echo "Staged files review — proceed? (y/n)"
```

## Documentation Validation

Applied before committing in both modes.

```bash
STAGED_FILES=$(git diff --cached --name-only)
CODE_FILES=$(echo "$STAGED_FILES" | grep -vE '\.(md|txt)$' || true)

# Warn if code changed but CHANGELOG missing
if [ ! -z "$CODE_FILES" ] && ! echo "$STAGED_FILES" | grep -q "CHANGELOG.md"; then
  echo "⚠️ Code changed but CHANGELOG.md not staged. Continue? (y/n)"
fi
```

## Auto-exclude Rules

Always exclude from commits:
- `.gitignore` patterns (temp files, build artifacts, virtual envs)
- Temp files: `*.pyc`, `.DS_Store`, `.cache/`, `.pytest_cache/`
- Virtual envs: `.venv/`, `venv/`, `env/`
- Build artifacts: `dist/`, `build/`, `*.egg-info/`
- Claude artifacts: `*.claude`, `*.analysis`, `*.report`, `*.debug`
