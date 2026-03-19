---
name: review-pull-request
description: Reviews GitHub pull requests comprehensively. Triages existing review comments, performs independent code review, runs tests, validates manual testing, checks Jira/issue coverage. Use when the user asks to review a PR, check a PR, or audit PR readiness.
allowed-tools: "Bash(gh pr*), Bash(gh issue*), Bash(gh run*), Read, Grep, Glob"
argument-hint: [owner/repo#number or PR URL]
---

# PR Review

## Review stance

Determine mode before starting. The agent picks based on signals; user can override at any time.

### Ship-it mode (pragmatic)
- Focus on critical/blocking issues only
- Consolidate all NITs into one "optional follow-up" list at end of review
- No change requests for style, naming, or minor refactoring
- Bias toward approval with conditions

### Polish mode (thorough)
- Request NIT fixes in-PR via inline comments
- Suggest refactoring, ask for more tests, give per-file detailed feedback

### Detection signals

**Ship-it** (any of): user says "urgent" / "too many rounds" / "skip NITs" / "focus on critical"; PR has many existing review rounds or comments; PR is weeks old; user explicitly says not looking for perfection.

**Polish** (default): fresh PR / first review round; user asks for thorough review without urgency; small focused PR.

**Default**: polish mode. If signals are ambiguous, confirm stance with user before proceeding.


## Review checklist

Work through all phases. Phases 1–2 can run in parallel using batch tool calls.

### Phase 1 — Context gathering

Use the **github** skill for all GitHub reads:
- PR metadata, diff, all review comments including **outdated** threads
- PR description and body comment thread for manual test evidence
- Check status via `gh pr checks <n> --repo <r>`; for failing checks, fetch logs with `gh run view <run-id> --log-failed`

Use the **jira** skill for ticket context if the PR links a Jira ticket **and jira is installed; skip this step otherwise**.

Check workspace `CLAUDE.md` / `AGENTS.md` for a `## PR Review` section with repo-specific checks. Apply those checks alongside this generic checklist.

**Cross-repo impact** (pipelines, scripts, configs referenced by the PR): check for a local clone before fetching via `gh api`. Local reads are faster and work offline.

### Phase 2 — Comment triage

For each existing review comment thread (including outdated):
- Check if the issue is addressed in the latest diff
- Classify: `can resolve` (addressed or correctly dismissed) vs `still needs fix`

Present the triage list to the user before taking any action. Only resolve threads after explicit user approval. Use the **github** skill's resolve-thread command.

### Phase 3 — Independent code review

Review the diff for:
- **Correctness**: logic bugs, edge cases, off-by-one errors
- **Error handling**: swallowed errors (`if err == nil { use(result) }` pattern), missing validation, silent failures
- **Tests**: coverage of new/changed behavior, missing edge cases
- **Consistency**: patterns matching the rest of the codebase, DRY violations, duplicate code blocks
- **Security**: secrets handling, permissions, injection vectors
- **Maintainability**: readability, naming clarity, complexity — would a newcomer understand this code in 6 months?
- **Documentation**: New or non-trivial functions have comments or docstrings; new pipelines/automation/features are documented.
- **Logging / observability**: Logs show *what* was checked (e.g. URLs tested, entities validated, counts), not only high-level "X OK".
- **Scope / design**: For scheduled jobs or broad scope, consider asking whether frequency/scope is necessary.
- **Process / sustainability**: For validation automation, consider whether there is a documented way to keep it in sync as the codebase grows.
- **Security / permissions**: ⚠️ If the PR modifies `CLAUDE.md`, `settings.json`, or permission files, flag as **CRITICAL** — review for unsafe loosening of restrictions or permission escalation
- **Cross-codebase patterns**: If you flag a pattern issue (e.g., broad exception handler, missing validation), grep the full codebase for the same pattern. Include findings in your review comment to help the author fix all occurrences, not just the flagged line

Inline comment placement rule: comment only on lines **actually changed by the PR**, not on unchanged context lines visible in the diff hunk.

### Phase 4 — Test execution

Run unit tests for the changed code. Use the repo's test runner (check `CLAUDE.md` / `AGENTS.md`). Report pass/fail with output. If tests fail, investigate and note whether it is a pre-existing failure or introduced by this PR.

### Phase 5 — Manual test assessment

- Review what manual tests are claimed in the PR description and comments
- Identify gaps; if they can be filled without the PR author, do it
- Propose any remaining manual tests with exact commands

### Phase 6 — Jira / issue alignment

If a Jira ticket or GitHub issue is linked **and the jira skill is available**:
- Compare PR changes against the ticket's acceptance criteria / expected outputs
- Flag any ticket requirements not covered by the PR

### Phase 7 — Final output

**Severity labels**:
- **Critical** (must fix before merge)
- **Suggestion** (consider fixing)
- **NIT** (nice to have, low priority)

When listing NITs, consider: function comments/docstrings, unit tests for new logic, logging that shows what was checked, documentation for new pipelines/features, and a process to keep validation in sync.

**Ship-it mode output**: single review comment with critical items, followed by one consolidated "optional follow-up NITs" block. No separate inline comments for NITs.

**Polish mode output**: inline comments per finding, plus a summary comment.

**Default**: output the review text in chat for the user to copy-paste via the GitHub UI. Only post directly via `gh pr review` or `gh api` if the user explicitly asks.

Tone: concise and informal.


## Write operations

- **Resolving threads**: only after user approves the Phase 2 triage list. Never resolve pre-emptively.
- **Posting review**: output text in chat by default. Only call `gh pr review` or post comments via `gh api` when user explicitly requests it.
- **No merging**: never merge a PR via CLI unless explicitly asked.


## Backport rules

Detect backport: check if `labels` contains `backport` (fetch via `gh pr view <n> --repo <r> --json labels`).

For backport PRs:
- **Only flag** issues new or different due to the target branch (merge conflicts, wrong branch assumptions, stale TODOs referencing unmerged PRs)
- **Do not re-flag** NITs/suggestions already present and approved in the original PR


## Disclaimer rule

When posting a review or comment whose body was **generated by the agent**, append `_Comment generated by Claude_ (or other agent name)` to the body. When posting text provided **verbatim by the user**, do not add the disclaimer.


## Subagent output mode

When invoked as a subagent by `triage-pull-requests`, return the following structured report instead of free-form text. Do NOT post any GitHub comments — the parent handles all posting.

```
PR: <owner/repo>#<n>
Author: @<handle>
Type: feature | backport | fix | cleanup | chore
Verdict: Looks OK | Needs changes | Needs more looking
Findings:
  Critical: <bullet list, or "none">
  Suggestions: <bullet list, or "none">
  NITs: <bullet list, or "none">
  Improvements: <optional proactive suggestions beyond the diff>
Tests: passed | failed | skipped | n/a
```

On error (PR not found, access denied, etc.):

```
PR: <owner/repo>#<n>
Error: <short reason>
Verdict: Error
```
