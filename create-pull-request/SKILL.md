---
name: create-pull-request
description: Creates and updates GitHub pull requests. Covers PR template usage, title/body preferences, and all instructions for creating a PR.
allowed-tools: "Bash(gh pr*)"
---

# Create Pull Request

This skill covers **creating (and updating) GitHub pull requests** using the GitHub CLI (`gh`). For how to run `gh` (commands, repo selection, auth, read-only usage), see the **github** skill.

## Always follow the repo PR template

- **If the repo has a pull request template in the `.github/` folder**, always use it.
- Common paths: `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, or templates in `.github/PULL_REQUEST_TEMPLATE/`. Check the repo to find the template.
- Use the template's **section headings** and **checklist** in the PR body. Fill in each section; keep any links (e.g. Contributing guide) at the bottom.
- **If there is no template**, still apply this skill's title and body preferences (scoped title, bullet list for changes, impact as lists, optional checklist).
- Do not add or change the template file itself unless the user explicitly asks.

## Instructions for creating a PR

- **Create as draft by default** unless the user asks for a ready-for-review PR.
- **Issue linkage**: If there is an issue, ask whether the PR should `Closes #X` or `Addresses #X` (or equivalent) and add that to the body or use `gh pr create --fill` where appropriate.
- **Repo**: Use the **github** skill for repo selection (e.g. `--repo <owner/repo>` when the PR is not in the current git repo).
- **Test plan**: Infer from the change surface; run the smallest sufficient set of checks and record commands/results in the PR when relevant.
- **Write operations**: Creating or editing a PR is a write operation; ensure the user has requested it or approved it (see the github skill for approval defaults).
- **Branch base**: Always branch from the repo's default base branch (usually `main`) explicitly — `git checkout -b <branch> main` — unless explicitly asked to branch from elsewhere. Never branch from whatever happens to be the current branch, as unrelated commits from that branch will appear in the PR diff.
- **Multiple PRs in one session**: when creating PRs in multiple repos, `git checkout <branch>` into the correct branch before each `gh pr create` call — `gh` resolves branch from the current checkout.

## Title preferences

- **Short, scoped, action-oriented.** Prefer: `Scope: what the PR does`.
- Examples: `CLI: add retry flag for transient errors`, `Pipelines: add step for X`.
- Human-readable summary, not a raw Conventional Commit line.
- No ticket prefixes in the title unless the team convention for that repo requires it.

## Body preferences

- **Describe your changes**: Short **bullet list**. One bullet per main change; concise phrasing; no long paragraphs.
- When updating a PR description, prefer a high-level, behavior/impact-focused change list (what changes for PR builds vs main), not a detailed accounting of code edits.
- Avoid bold/emphasis formatting in the PR body unless explicitly requested.
- When the change has **measurable impact** (performance, which jobs/hooks run, etc.): add a short **impact** block with before/after or what is skipped. Use **lists and sub-bullets**, not tables.
- **Issue ticket**: Include the section from the template (e.g. "Issue ticket number and link"); use N/A when there is no ticket.
- **Checklist**: Use `- [ ]` or `- [x]` per actual state; keep the template checklist and links at the bottom.

## Example structure (with template sections)

```markdown
## Describe your changes

- Extract dependency installation into a dedicated setup script
- Reuse existing virtualenv when requirements files are unchanged (content hash check)
- Skip expensive validation step when unrelated files change

**Pre-commit duration for typical commit:**
- **Before this PR:** ~49s total (setup reinstalled deps every run; validation ran on every commit)
- **After this PR:** ~12s total (setup reuses existing env when deps unchanged; validation is skipped)

## Issue ticket number and link

N/A

## Checklist before requesting a review
- [ ] I have read the [Contributing guide].
- [ ] ...
```

## Relation to github

- **github**: CLI usage — `gh pr create` / `gh pr edit`, repo selection, auth, draft/ready conversions.
- **create-pull-request**: what to put in the PR — template, title/body preferences, draft by default, issue linkage, test plan.
