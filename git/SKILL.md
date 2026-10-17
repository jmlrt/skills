---
name: git
description: "Git workflow conventions: worktrees, commits, rebase, pre-commit hooks, and pushing branches. Use before starting code changes in a repo, and whenever committing, rebasing, or pushing."
---

# Git workflow

## Worktrees (all code changes)

Not required for doc-only repos (listed in your user-level CLAUDE.md).

- Run `git worktree list` at session start, after a summary, and before creating one; reuse what exists. A
  `.worktrees/<name>/.git` pointing nowhere is a dead leftover, safe to `rm -rf`.
- Create BEFORE any edit, at `.worktrees/<name>` (name = branch with `/` → `-`; `.worktrees/` is globally ignored).
  Run `git worktree add` from the repo root after an absolute `cd`, never with `-C`.
- If edits already landed in the main checkout: `git stash`, create the worktree, `git stash pop` inside it.
- Start point:
  - New branch: local `main` (`git worktree add .worktrees/fix-foo -b fix/foo main`), since it may hold unpushed
    commits. If `git log main..origin/main --oneline` shows it's stale, `git fetch origin main` and use
    `origin/main`.
  - Existing remote branch: same local name, e.g. `git worktree add .worktrees/bootstrap-foo -b bootstrap/foo
    origin/bootstrap/foo`.
- Always Read/Edit/Write through the worktree's absolute path — main-checkout paths edit main silently. Use
  `git -C <abs path>` across Bash calls (CWD persists between calls).
- After merge: `git worktree remove .worktrees/<name> && git branch -d <branch>`. For repos outside the primary CWD
  this fails in the sandbox: give the user one `! <command>` per repo/branch instead of a cleanup script.

## Commits

- Imperative, present tense (`add X`, `fix Y`), subject ≤72 chars; body explains WHY if non-obvious.
- Branch names: kebab-case, scoped to the change (`fix-release-tag-parsing`).
- Amending prior work: `fixup!` / `squash!` commits (`autosquash = true`).
- pre-commit must pass; run `pre-commit run` if hooks aren't installed.
- Formatter hooks (shfmt, black, end-of-file-fixer) fix files in place when they fail the commit: `git add` the
  reformatted files and retry.

## Rebase

- Rebase, never merge commits on feature branches (`pull.rebase = true`).
- Non-interactive only: `GIT_EDITOR=true git rebase ...` (`-i` hangs, `--no-edit` is invalid for rebase).
- After resolving conflicts, audit for orphaned files, stale TODOs about merged PRs, and dead imports.

## Pushing

- New branches: explicit refspec `git push -u origin <name>:<name>`. `push.default=upstream` otherwise targets the
  start-point branch. Verify with `gh api repos/<o>/<r>/branches/<name>`, not the push output.
- "Bypassed rule violations for refs/heads/<branch>" in push output means the push landed on a protected branch
  without review: stop and verify immediately.
