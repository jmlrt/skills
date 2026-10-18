---
name: git-repos-cleanup
description: "Clean up stale git worktrees and local branches across many local clones. Use when asked to prune, clean up, or delete old worktrees or local branches that are pushed or merged, in one repo or in every repo under a directory."
---

# Git repos cleanup

Removes worktrees and local branches whose work is already on a remote. Anything that could lose work is reported and
needs explicit approval.

## Scope

- Repos: every clone under the directory the user names (ask if unknown), or the single repo given.
- Run `git -C <repo> fetch --prune` first. A stale remote-tracking ref for a branch deleted on the remote still contains
  its commits, so `branch -r --contains` would call the branch pushed when the only copy is local. Pruning only touches
  local refs. If the fetch fails, treat that repo's "pushed" results as unreliable and keep its branches.
- Use `git -C <repo>`; do not `cd` between repos.
- Never print remote URLs: clones can embed credentials. Derive the `owner/repo` slug in a pipe without echoing it.

## 1. Worktrees

List extra worktrees per repo (`git worktree list --porcelain`, skipping the first entry, the main checkout). For each:

- Dirty: `git -C <wt> status --porcelain` is non-empty.
- Unpushed: `git -C <wt> log --oneline HEAD --not --remotes` is non-empty. A detached HEAD is judged the same way.

Remove clean and fully pushed worktrees with `git worktree remove <wt>` (no `--force`; it refuses if dirty). Keep the
branches. List the dirty or unpushed ones to the user. Use `--force` only after they approve those specific
worktrees, because uncommitted changes are lost. Afterwards `rmdir` an emptied worktree directory (such as
`.worktrees/`); it refuses if anything is left.

## 2. Local branches

Skip the checked-out branch, `main`/`master`, and any branch checked out in a worktree (git refuses to delete it).

**Pushed.** If `git branch -r --contains <tip>` (ignoring `HEAD ->` lines) is non-empty, `git branch -D <branch>` is safe
because the commits survive on the remote.

**Merged by PR.** Squash and rebase merges are invisible to ancestry checks, so for the remaining branches ask the
forge:

```bash
gh pr list -R <owner/repo> --head <branch> --state all --json number,state,headRefOid
```

- A `MERGED` PR whose `headRefOid` equals the local tip: delete.
- A `MERGED` PR with a different tip: the branch has commits the PR never saw (amend, rebase, later work). List them
  and delete only after the user approves; the commits remain only in the reflog.
- No PR, or only `CLOSED` PRs: go to step 3 instead of deleting. They may hold unreviewed work.

## 3. Triage the rest

Survey each leftover branch in one line: last commit date, `git rev-list --count <default>..<branch>`, `[gone]`
upstream, and whether `git branch -r --contains <tip>` is empty. Then:

- **Review checkouts.** A branch named `pr-N`, `review-N` or `*-review` is a local copy of someone else's PR, and
  `--head <branch>` finds nothing for it. Look the PR up by number (`gh pr view N -R <owner/repo>`). If it is merged,
  delete the branch whatever its tip, since the work is upstream.
- **Duplicates.** Identical tips, or a `-rebase`/`-clean`/`-rewrite` copy of a branch already merged or kept: keep one.
- **Content check.** `git cherry` cannot see squash merges, so search the default branch for the files or commands the
  branch adds. Present means superseded: delete. Missing means unmerged work: list it for the user. This is a
  judgement, not proof; say so.
- **No merge base** with the default branch (orphan history): look at it manually.

## 4. Other leftovers

Branch cleanup skips the checked-out branch, so also survey each repo for these. Report them; act only on approval.

- **Finished current branch.** The checked-out branch has a merged or closed PR, or its tip is on a remote. Once the tree
  is clean and nothing is unpushed, switch to the default branch (never `--force`, so uncommitted changes carry over
  or the switch refuses) and delete it. Check what carried over.
- **Stashes.** List age, base branch and `git stash show --stat`. Old stashes on dead branches are usually trivial or
  regenerable. To test whether one landed, compare the lines it adds with the default branch, because the default has
  moved on and a whole-file or patch-apply comparison reports false divergence. A dropped stash is not restorable in
  the normal way, so print its SHA first (`git stash store <sha>` brings it back).
- **Dirty or unpushed default-branch checkouts, untracked files.** Report only. Untracked files can be local content
  that exists nowhere else, so never delete them without a specific go-ahead.
- **Archived upstreams.** `gh repo view <owner/repo> --json isArchived,isFork` flags clones of archived repos and forks.
  List them; whether to delete the clone is the user's call.
- **Large ignored artifacts.** For the biggest working trees, list the largest entries from
  `git status --porcelain --ignored` with sizes (virtualenvs, `node_modules`, build output, toolchain caches). Report
  only: never run `git clean -x`, and treat toolchain caches as needed.

## 5. Report

End with, per category: removed, kept and why, and anything the user must run themselves. Print the tip SHA of every
deleted branch so it can be restored with `git branch <name> <sha>` from the reflog. Flag deleted branches whose commits
are on no remote. Offer follow-ups for the kept branches rather than acting on them.

## Notes

- Do one pass per repo in a script (survey, then delete) and write its output to a scratch file so the summary comes
  from data, not memory. Use positional values or functions in zsh: unquoted `$var` does not word-split, and
  `path`/`status` are reserved names.
- If the environment blocks writes in some repos (permission errors on `git worktree remove` or `git branch -D`), or a
  permission layer denies a batch delete, do not retry in smaller pieces. Give the user one self-contained command
  block that defines its own helper and variables.
- Dropping stashes shifts the indices of the rest: drop from the highest index down, and do not reuse an index after a
  drop.
- Verify afterwards: `git worktree list` shows only the main checkout, and the kept-branch list matches the report.
