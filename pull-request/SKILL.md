---
name: pull-request
description: "Create and update pull requests as an author. Use when you're ready to propose changes: creates PRs with comprehensive file validation, tests, commit messages, and PR descriptions. Also guides addressing reviewer feedback through iterative fixes and comment resolution."
allowed-tools: "Bash(git:*), Bash(gh:*), Bash(grep:*), Bash(jq:*), Bash(make:*), Read, Edit, Write, Glob, AskUserQuestion"
argument-hint: [branch-name]
disable-model-invocation: true
---

# Pull Request Workflow (Author)

| Mode | Triggers |
|------|----------|
| **Create** | "create a PR", "open a PR", "submit for review" |
| **Iterate** | "address PR review", "fix PR feedback", "address review comments" |

Reviewers use the **review-pull-request** skill.

## Create

1. Branch from the repo's default branch explicitly (`git checkout -b <branch> origin/<default>`) and rebase on it before pushing.
2. Ask which files to stage; stage only those. Never stage temp files, agent artifacts, build output, or secrets.
3. Run the repo's pre-commit hooks and test/lint targets (skip tests for docs-only changes). Update CHANGELOG/README when the repo expects it.
4. Show the commit message, title, and body, then ask: "Ready to push and create the PR?" Proceed only on an explicit yes.
5. Push and create a **draft** PR by default (`gh pr create --draft --body-file <file>`). Keep temp message files out of the repo.

**Cross-fork PRs**: `gh pr create --head fork:branch --repo upstream` fails with "not all refs are readable" when upstream doesn't know the fork. Push to the fork, then `gh pr create --repo upstream --head <user>:<branch>`.

### Title

Short, scoped, action-oriented: `Scope: what the PR does` (e.g. `CLI: add retry flag for transient errors`). Human-readable, not a raw Conventional Commit line; no ticket prefix unless the repo requires it.

### Body

- **Use the repo's PR template** (`.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/`) if present; fill each section, keep its links at the bottom, don't edit the template. Otherwise mirror a recent merged PR (`gh pr view <N>`).
- **Outcome, not implementation**: what the change enables or replaces, not how the code works. Reviewers can read the diff.
- **Only what the diff does and why**: leave investigation side-findings for chat or the tracking issue.
- Feature/fix: short bullet list, one per main change. Refactor: brief Problem → Solution → Impact narrative.
- Add an impact block (before/after) when the change is measurable.
- Link the tracking issue (`owner/repo#N` cross-repo). If none is obvious, ask before writing N/A.
- Checkboxes reflect actual state and cover only what can be verified before merge. Post-merge steps (release, downstream bump) go in a plain-bullet "Follow-up" section.

```markdown
## Describe your changes

- Extract dependency installation into a setup script
- Reuse the existing virtualenv when requirements are unchanged

**Pre-commit duration:** ~49s before, ~12s after

## Issue ticket

Closes #123

## Checklist before requesting a review
- [x] Tests pass locally
```

## Iterate

1. Find the PR for the current branch (`gh pr view --json number`).
2. Fetch all review threads, including inline comments (`gh pr view` omits them; use `gh api repos/<o>/<r>/pulls/<n>/comments` or GraphQL `reviewThreads` for thread ids and resolution state).
3. Triage each as must-fix, enhancement, or NIT and get user approval on what to fix.
4. Apply fixes. For each pattern flagged, search the codebase for the same pattern and fix all occurrences rather than waiting for the next review round. Treat changes to agent instructions, settings, or permission files as sensitive.
5. Stage only the intended files, run pre-commit and tests, commit, and push (no force push unless you rebased; then `--force-with-lease`).
6. Resolve addressed threads (GraphQL `resolveReviewThread`) and reply where a comment was declined or needs explanation. Summarize what was fixed, skipped, and why.

## Mark ready for review

Before undrafting or requesting review:

- Run the tests relevant to the changed files. Check repo agent instructions (`AGENTS.md`, `CLAUDE.md`) for a `## PR Review` section listing repo-specific checks. For scripts, exercise the happy path, the rejection path, and empty/missing inputs.
- Post the evidence as a PR comment, for example:

```
| Test | Scenario   | Result |
|------|------------|--------|
| T1   | happy path | pass   |
| T2   | rejection  | pass   |
```

- State explicitly what couldn't be run locally (live infra, secrets, full pipeline) so reviewers know the coverage gap.
- Then undraft (`gh pr ready`) and request review, after user confirmation.
