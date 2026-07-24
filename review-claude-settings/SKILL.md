---
name: review-claude-settings
description: Audit Claude Code settings.json files — global (~/.claude/settings.json) and per-repo (.claude/settings.json, .claude/settings.local.json) — for permission consolidation, redundancy, and security risks. Use when asked to "review settings.json", "audit claude settings", "clean up permissions", "check what should be global vs repo", or "security review of settings".
allowed-tools: Read, Glob, Bash(find:*), Bash(grep:*), Bash(jq:*), Bash(ls:*), Edit, Write
---

# Review Claude Settings

Audits all `settings.json` / `settings.local.json` files and produces a structured findings report. Changes require explicit confirmation before applying.

Before editing global settings, resolve `~/.claude/settings.json` with `readlink`. If it is a symlink, edit its target rather than the symlink.

## Scope

1. **Global**: `~/.claude/settings.json`
2. **Per-repo project settings**: `.claude/settings.json` under the user-provided workspace root (all depths)
3. **Per-repo local settings**: `.claude/settings.local.json` under the user-provided workspace root (all depths) — machine-local, never committed

---

## Phase 1: Discovery

Run in parallel:

```bash
# Find all project settings files
find <workspace-root> -maxdepth 5 -name "settings.json" -path "*/.claude/*" 2>/dev/null | sort
find <workspace-root> -maxdepth 5 -name "settings.local.json" -path "*/.claude/*" 2>/dev/null | sort
```

Then read all discovered files in parallel, including the global settings file.

---

## Phase 2: Consolidation Analysis

Compare permissions across all files to identify:

**Should be global** — a permission appears in 3+ repos, or is clearly tool-agnostic (e.g. `Bash(grep *)`, `Bash(jq *)`, `Bash(ls *)`, `Bash(git log *)`, `Bash(gh pr list *)`). Flag for promotion to global `settings.json`; then remove from each repo file.

**Duplicates global** — permission already present verbatim in the global file. Remove from the repo file.

**Repo-specific** — permission only makes sense in this specific repo (e.g. `Bash(terraform plan *)`, `Bash(aws ecs *)`, cloud-provider CLI calls). Keep in repo file.

**`settings.local.json` entries** — review whether they're truly machine-local or accidentally one-off approvals. If they enumerate individually approved specific invocations (e.g. `Bash(git push origin feature-x:*)`) rather than general rules, flag as stale.

---

## Phase 3: Security Audit

Apply this checklist to the **global** settings file first, then each repo file.

### Critical risks — pre-approve with no argument restriction

| Pattern | Risk | Mitigation |
|---------|------|------------|
| `Bash(cat *)` | Reads any file on disk, bypassing tool path restrictions (for example, credential files or `.env`). | Remove; use the agent's scoped file-reading tool. |
| `Bash(git *)` wildcard | Pre-approves `git push --force`, `git reset --hard`, `git clean -fdx`, `git config --global`. CLAUDE.md policy says "never push without explicit instruction". | Replace with enumerated safe subcommands (see safe list below). |
| `Bash(gh *)` wildcard | Pre-approves `gh pr merge`, `gh pr comment`, `gh api *`, `gh repo delete`, `gh secret set`. CLAUDE.md policy says "always ask before posting to GitHub". | Replace with enumerated read-only subcommands (see safe list below). |
| `Bash(find *)` | `-exec` flag turns find into an arbitrary command executor. | Remove from global; add specific `Bash(find <path> -name * -type *)` patterns at repo level if needed. |

### High risks — wildcard over a powerful tool

| Pattern | Risk | Mitigation |
|---------|------|------------|
| `Bash(make *)` | Runs arbitrary Makefile targets in any repo — could trigger deploys, destructive clean operations, or custom targets. | Replace with explicit safe targets: `make build`, `make check`, `make clean`, `make fmt`, `make generate`, `make help`, `make lint`, `make test`. |
| `Bash(curl *)` | Exfiltrates data or calls external APIs without review. Combine with `excludedCommands` bypass makes it fully unsandboxed. | Move to repo-level with specific target restrictions; or require prompt. |
| `Bash(python3 *)` / `Bash(node *)` | Executes arbitrary scripts. | Move to repo-level only. |

### Medium risks

| Pattern | Risk | Mitigation |
|---------|------|------------|
| `enableWeakerNetworkIsolation: true` | Defeats sandbox network isolation — allows outbound connections beyond `allowedDomains`. | Remove unless strictly required; document why if kept. |
| `Bash(sed *)` | In-place editing of any file (`sed -i`). Lower risk since Edit tool is preferred, but worth reviewing. | Acceptable if Read path restrictions are enforced; lower priority. |
| `Bash(uv *)` | Can install packages and modify environment. Acceptable for Python development but check scope. | Move to repo-level if only needed in Python repos. |
| Broad workspace read access | Reads every repository in the workspace. | Acceptable only when no narrower scope fits. |

### Policy vs permission gap check

For each of the following CLAUDE.md policies, verify no permission pre-approves the contradicted action:

- "Never push without explicit instruction" → `Bash(git push *)` must NOT be in allow list
- "Never merge via CLI" → `Bash(gh pr merge *)` must NOT be in allow list
- "Always ask before posting to GitHub" → `Bash(gh pr comment *)`, `Bash(gh issue comment *)` must NOT be in allow list
- "No secrets in code or commits" → no credential-exposing commands like `Bash(env)` with no path restriction

### excludedCommands review

`excludedCommands` bypasses the sandbox entirely (no network or filesystem restrictions). Any command listed here can reach any network host and read/write any file. Review each entry:

- Is it intentionally trusted (e.g. `git` because it uses SSH remotes, `gh` because it uses GitHub API)?
- Does the corresponding `Bash(cmd *)` allow list entry stay within the spirit of that trust?

---

## Phase 4: Safe Permission Reference Lists

Use these when replacing wildcards.

**`gh` read-only subcommands** (safe to pre-approve globally):
```
"Bash(gh issue list *)", "Bash(gh issue view *)",
"Bash(gh pr checks *)", "Bash(gh pr diff *)", "Bash(gh pr list *)", "Bash(gh pr view *)",
"Bash(gh release list *)", "Bash(gh release view *)",
"Bash(gh repo list *)", "Bash(gh repo view *)",
"Bash(gh run list *)", "Bash(gh run view *)", "Bash(gh run watch *)",
"Bash(gh status *)",
"Bash(gh workflow list *)", "Bash(gh workflow view *)"
```

**`git` safe subcommands** (safe to pre-approve globally — excludes push/reset/clean/config):
```
"Bash(GIT_EDITOR=true git rebase *)",
"Bash(git add *)", "Bash(git blame *)", "Bash(git branch *)",
"Bash(git cherry-pick *)", "Bash(git checkout *)", "Bash(git commit *)",
"Bash(git describe *)", "Bash(git diff *)", "Bash(git fetch *)",
"Bash(git log *)", "Bash(git merge *)", "Bash(git remote *)",
"Bash(git rev-parse *)", "Bash(git show *)", "Bash(git stash *)",
"Bash(git status *)", "Bash(git submodule *)", "Bash(git switch *)",
"Bash(git tag *)", "Bash(git worktree *)"
```

**`make` safe targets** (safe to pre-approve globally):
```
"Bash(make build *)", "Bash(make check *)", "Bash(make clean *)",
"Bash(make fmt *)", "Bash(make generate *)", "Bash(make help *)",
"Bash(make lint *)", "Bash(make test *)"
```

---

## Phase 5: Report

Present findings as structured tables before any changes. Group by severity:

```
## Findings

### Critical
| # | File        | Permission         | Risk                          | Proposed fix            |
|---|------------|-------------------|-------------------------------|-------------------------|
| 1 | global      | Bash(cat *)        | Reads sensitive files outside Read restrictions | Remove |
| 2 | global      | Bash(git *)        | Pre-approves git push/reset/clean | Replace with safe list |

### High
| # | File        | Permission         | Risk                          | Proposed fix            |
|---|------------|-------------------|-------------------------------|-------------------------|

### Medium
| # | File        | Permission         | Risk                          | Proposed fix            |
|---|------------|-------------------|-------------------------------|-------------------------|

### Consolidation
| # | Permission         | Present in                            | Proposed fix                 |
|---|-------------------|---------------------------------------|------------------------------|
| 1 | Bash(jq *)         | repo-a, repo-b, repo-c               | Move to global; remove from repos |
| 2 | Bash(gh pr list *) | global + repo-d                      | Remove from repo-d (duplicate) |
```

If no findings in a category, state "No findings."

---

## Phase 6: Apply (with confirmation)

After presenting the report, ask: **"Apply all? Or specify which numbers to apply."**

- For global changes, edit the target of `~/.claude/settings.json` when it is a symlink.
- Use targeted `Edit` calls per finding; do not rewrite entire files.
- Re-read each edited section after applying to confirm the change landed.
- Do not create `settings.json` files that did not previously exist — if a repo has no `.claude/settings.json`, skip it.

---

## Constraints

- Never rewrite an entire settings file unless the user explicitly asks.
- Never silently remove a permission — always show the proposed change first.
- `settings.local.json` is machine-local; never commit it; treat stale one-off entries as low priority unless the user asks to clean them up.
- When in doubt about whether a permission is safe, flag it rather than silently keeping it.
