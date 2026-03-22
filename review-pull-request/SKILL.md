---
name: review-pull-request
description: "Review pull requests as a reviewer. Use when validating a PR before merge: performs independent code review, runs tests, validates manual testing. Handles single PRs with detailed analysis or multiple PRs in parallel batch mode with summary triage table."
allowed-tools: "Bash(gh pr*), Bash(gh issue*), Bash(gh run*), Read, Grep, Glob"
argument-hint: [owner/repo#number, PR URL, or multiple]
disable-model-invocation: true
---

# PR Review (Reviewer)

This skill reviews pull requests as a reviewer. Authors use the **pull-request** skill to create and update PRs, then request review.

## Single vs. Multiple PRs

**Single PR**: Provide one `owner/repo#123` or PR URL → Full detailed review (7 phases).

**Multiple PRs**: Provide list like `owner/repo#123 owner/repo#456` or `owner/repo#123, owner/repo#456` → Parallel batch triage (phases below).

---

## Review stance

Default to **polish mode** (thorough review). User can request **ship-it mode** (pragmatic) at any time.

### Polish mode (default)
- Request NIT fixes in-PR via inline comments
- Suggest refactoring, ask for more tests, give per-file detailed feedback
- Consolidate findings into a detailed summary comment

### Ship-it mode (pragmatic)
- Focus on critical/blocking issues only
- Consolidate all NITs into one "optional follow-up" list at end of review
- No change requests for style, naming, or minor refactoring
- Bias toward approval with conditions

**How to request ship-it**: Say "urgent" / "pragmatic" / "focus on critical" / "skip NITs".


---

## Single PR Review Checklist

Work through all phases. Phases 1–2 can run in parallel using batch tool calls.

### Phase 0: Author self-check (before review)

If you're an author preparing for review, consider checking before requesting review:

- [ ] All tests passing locally (`make check`)
- [ ] No secrets, temp files, or artifacts staged
- [ ] Code changes include CHANGELOG.md/documentation
- [ ] No unresolved issues in your own review

**Note**: Reviewers will check this during Phase 3 anyway, so this is optional. Skip if your changes are ready.

---

### Phase 1: Context gathering

Use the **github** skill for all GitHub reads:
- PR metadata, diff, all review comments including **outdated** threads
- PR description and body comment thread for manual test evidence
- Check status via `gh pr checks <n> --repo <r>`; for failing checks, fetch logs with `gh run view <run-id> --log-failed`

Use the **jira** skill for ticket context if the PR links a Jira ticket **and jira is installed; skip this step otherwise**.

Check workspace `CLAUDE.md` / `AGENTS.md` for a `## PR Review` section with repo-specific checks. Apply those checks alongside this generic checklist.

**Cross-repo impact** (pipelines, scripts, configs referenced by the PR): check for a local clone before fetching via `gh api`. Local reads are faster and work offline.

### Phase 2: Comment triage

For each existing review comment thread (including outdated):
- Check if the issue is addressed in the latest diff
- Classify: `can resolve` (addressed or correctly dismissed) vs `still needs fix`

Present the triage list to the user before taking any action. Only resolve threads after explicit user approval. Use the **github** skill's resolve-thread command.

### Phase 3: Independent code review

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

### Phase 4: Test execution

Run unit tests for the changed code. Use the repo's test runner (check `CLAUDE.md` / `AGENTS.md`). Report pass/fail with output. If tests fail, investigate and note whether it is a pre-existing failure or introduced by this PR.

### Phase 5: Manual test assessment

- Review what manual tests are claimed in the PR description and comments
- Identify gaps; if they can be filled without the PR author, do it
- Propose any remaining manual tests with exact commands

### Phase 6: Jira / issue alignment

If a Jira ticket or GitHub issue is linked **and the jira skill is available**:
- Compare PR changes against the ticket's acceptance criteria / expected outputs
- Flag any ticket requirements not covered by the PR

### Phase 7: Final output

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

When posting a review or comment whose body was **generated by the agent**, append `_Comment generated by Claude_` to the body. When posting text provided **verbatim by the user**, do not add the disclaimer.


---

# Parallel Triage Mode (Multiple PRs)

When reviewing multiple PRs, orchestrate in parallel.

## Phase 1: Parse and validate

Parse PR inputs (handles `owner/repo#123`, `https://github.com/owner/repo/pull/123`, bare `#123` with git remote inference).

Validate that each PR exists with `gh pr view <owner/repo>#<n> --json number,title,author,url`.

## Phase 2: Parallel dispatch

Launch **one subagent per PR in a batch** using the Agent tool. Each subagent:
- Reviews the single PR using the "Single PR Review Checklist" (Phases 0-7 above)
- Returns a structured report (see format below)
- Does NOT post any GitHub comments

**Subagent permission**: Subagents inherit `allowed-tools` from this skill. If a subagent fails on Bash permissions, the parent can retry sequentially (slower but same outcome).

## Phase 3: Summary table

After all subagents return, display a compact triage table:

```
| PR                                 | Author    | Verdict       | Critical | Suggestions | NITs |
|------------------------------------|-----------|---------------|----------|-------------|------|
| [owner/repo#123](https://...)       | @author1  | Looks OK      | —        | 1           | 2    |
| [owner/repo#456](https://...)       | @author2  | Needs changes | 2        | 0           | 1    |
| [owner/repo#789](https://...)       | @author3  | Error: 404    | —        | —           | —    |
```

Then list findings per PR (Critical → Suggestions → NITs → Improvements), aligning with the NIT guidelines above. Ask the user for decisions.

## Phase 4: User decisions

Valid responses (blanket or per-PR):
- `approve`, `approve all that look OK`
- `request-changes <reason>`
- `comment <text>` — post a comment without a verdict
- `skip` / `skip all` — do nothing

**Post nothing without an explicit decision.**

## Phase 5: Post reviews

For approved PRs, post reviews via `gh pr review`. For request-changes, use `gh pr review --request-changes`. Follow the disclaimer rule.

**Inline comments**: If the user wants per-line feedback, prefer the **github** skill's "Inline comments via REST API" recipe (`POST /pulls/<n>/reviews`).

---

## Subagent report format

When a subagent reviews a single PR, return this structured report:

```
PR: owner/repo#123
Author: @handle
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
PR: owner/repo#123
Error: <short reason>
Verdict: Error
```
