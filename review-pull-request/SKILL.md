---
name: review-pull-request
description: Reviews GitHub pull requests comprehensively. Triages existing review comments, performs independent code review, runs tests, validates manual testing, checks Jira/issue coverage. Use when the user asks to review a PR, check a PR, or audit PR readiness.
allowed-tools: "Bash(gh:*), Read, Grep, Glob"
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

---

## Review checklist

Work through all phases. Phases 1–2 can run in parallel using batch tool calls.

### Phase 1 — Context gathering

Use the **github** skill for all GitHub reads:
- PR metadata, diff, all review comments including **outdated** threads
- PR description and body comment thread for manual test evidence

Use the **jira** skill for ticket context if the PR links a Jira ticket **and jira is installed; skip this step otherwise**.

Check workspace `CLAUDE.md` / `AGENTS.md` for a `## PR Review` section with repo-specific checks. Apply those checks alongside this generic checklist.

**Cross-repo impact** (pipelines, scripts, configs referenced by the PR): check for a local clone before fetching via `gh api`. Local reads are faster and work offline.

### Phase 2 — Comment triage

For each existing review comment thread (including outdated):
- Check if the issue is addressed in the latest diff
- Classify: `can resolve` (addressed or correctly dismissed) vs `still needs fix`

Present the triage list to the user before taking any action. Only resolve threads after explicit user approval. Use `gh api graphql` to resolve threads:

```bash
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) { thread { isResolved } } }'
```

### Phase 3 — Independent code review

Review the diff for:
- **Correctness**: logic bugs, edge cases, off-by-one errors
- **Error handling**: swallowed errors (`if err == nil { use(result) }` pattern), missing validation, silent failures
- **Tests**: coverage of new/changed behavior, missing edge cases
- **Consistency**: patterns matching the rest of the codebase, DRY violations, duplicate code blocks
- **Security**: secrets handling, permissions, injection vectors
- **Performance**: unnecessary allocations, N+1 patterns
- **Documentation**: New or non-trivial functions have comments or docstrings; new pipelines/automation/features are documented (what it does, where it lives, how to run it).
- **Logging / observability**: Logs show *what* was checked (e.g. URLs tested, entities validated, counts), not only high-level "X OK", so failures are debuggable from logs alone.
- **Scope / design**: For scheduled jobs, batch processing, or broad scope, consider asking whether frequency/scope is necessary (e.g. daily for all branches vs first week only).
- **Process / sustainability**: For validation or checklist-style automation, consider whether there is a documented way to keep the pipeline in sync when the set of validated items grows (e.g. "when we add new artifacts, how do we remember to add them to this pipeline?"). Suggest docs or a checklist if missing.

When suggesting NITs, prefer asking for: function-level comments/docstrings, unit tests for new non-trivial logic, more detailed logging (what was checked), documentation for new pipelines/features, and a process or checklist so validation stays in sync (e.g. new artifact types → update pipeline).

Inline comment placement rule:
- When leaving **inline review comments**, comment only on lines **actually changed by the PR** (added/modified lines in the diff),
  not on unchanged context lines that happen to be visible in the diff hunk.
- Exception: only comment on unchanged lines if the user explicitly asks to audit broader surrounding code.

### Phase 4 — Test execution

Run unit tests for the changed code. Use the repo's test runner (check `CLAUDE.md` / `AGENTS.md`). Report pass/fail with output. If tests fail, investigate and note whether it is a pre-existing failure or introduced by this PR.

### Phase 5 — Manual test assessment

- Review what manual tests are claimed in the PR description and comments
- Identify gaps: data validation against prod endpoints, pipeline output comparison, endpoint consistency checks
- If gaps exist and can be filled without the PR author (e.g., by fetching public prod data or generating pipeline YAML locally), do it
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

When listing NITs, consider including (when applicable): function comments/docstrings, unit tests for new logic, logging that shows what was checked (e.g. URLs/entities), documentation for new pipelines/features, and a process or checklist so validation stays in sync (e.g. new artifact types → update pipeline).

**Ship-it mode output**: single review comment with critical items listed, followed by one consolidated "optional follow-up NITs" block at the end. No separate inline comments for NITs.

**Polish mode output**: inline comments per finding, plus a summary comment.

**Default**: output the review text in chat for the user to copy-paste via the GitHub UI. Only post directly via `gh pr review` or `gh api` if the user explicitly asks.

Tone: concise and informal. Avoid over-formal bullet-per-finding structure for minor issues.

---

## Integration with other skills

- **github**: all GitHub reads (PR metadata, diff, review comments, issue comments). Try in sandbox first; no `full_network` needed for `gh` commands.
- **jira** (optional): linked ticket acceptance criteria and context. Skip if not installed.
- **create-pull-request**: reference for comment/review body style and formatting preferences.

---

## Write operations

- **Resolving threads**: only after user approves the Phase 2 triage list. Never resolve pre-emptively.
- **Posting review**: output text in chat by default. Only call `gh pr review` or post comments via `gh api` when user explicitly requests it.
- **No merging**: never merge a PR via CLI. Merges happen via the GitHub UI.

---

## Backport rules

Detect backport: check if `labels` contains `backport` (fetch via `gh pr view <n> --repo <r> --json labels`).

For backport PRs:
- **Only flag** issues new or different due to the target branch (merge conflicts, wrong branch assumptions, stale TODOs referencing unmerged PRs)
- **Do not re-flag** NITs/suggestions already present and approved in the original PR

---

## Disclaimer rule

When posting a review or comment whose body was **generated by the agent**, append `_Comment generated by Claude_` to the body. When posting text provided **verbatim by the user**, do not add the disclaimer.

---

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
