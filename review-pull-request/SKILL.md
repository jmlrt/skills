---
name: review-pull-request
description: "Review pull requests as a reviewer. Use when validating a PR before merge: performs independent code review, runs tests, validates manual testing. Handles single PRs with detailed analysis or multiple PRs in parallel batch mode with summary triage table."
allowed-tools: "Bash(git:*), Bash(gh:*), Bash(grep:*), Bash(make:*), Read, Glob"
argument-hint: [owner/repo#number, PR URL, or multiple]
---

# PR Review (Reviewer)

Authors use the **pull-request** skill. One PR (`owner/repo#123` or URL) gets the full single review; several PRs get parallel batch triage.

## Review stance

Default to **polish mode**; switch when the user asks.

- **Polish** (default): inline comments per finding, NITs requested in-PR, plus a summary comment.
- **Ship-it** ("urgent", "pragmatic", "skip NITs"): critical issues only, one review comment, NITs consolidated into an "optional follow-up" block, bias toward approval.
- **KISS/YAGNI** ("KISS", "simplify", "keep me honest"): after the correctness pass, ask "is this the simplest correct solution?" Flag unnecessary abstractions, speculative features, over-documented internals, structures where a scalar suffices.

## Single PR review

### Pre-flight: author check

Compare the PR author and every commit author against the requester (`gh api user`). GitHub doesn't let authors approve their own PRs, and a bot PR can carry a human fixup commit. If the requester authored it, say so first and offer to request another reviewer; don't do a full review only to flag this at the end.

### 1. Context

- PR metadata, diff, checks (`gh pr checks`; failing logs via `gh run view --log-failed`), and **all** review threads including outdated ones. `gh pr view` drops inline comments; fetch them via the API.
- Linked issue with its comments: anything it prescribes (scope, design, requested tests) isn't a finding, and uncovered requirements are.
- Repo agent instructions (`AGENTS.md`, `CLAUDE.md`) for a `## PR Review` section; apply those checks. Check whether README or agent instructions should have been updated alongside the change.
- Companion PRs in other repos: verify they're merged, and for release-dependent changes that a release was cut after the merge. An unmerged prerequisite is a Critical ordering issue.

### 2. Comment triage

For each existing thread, classify `can resolve` (addressed or correctly dismissed) or `still needs fix`. Judge the requester's own threads against the core ask, not every example in the comment. Present the list; resolve threads only after explicit approval.

### 3. Independent review

- Read the actual PR-branch file for substantive changes; diff hunk headers show the old enclosing function and can mislead.
- Read the full test function before claiming a table-driven case asserts the wrong thing; row names are documentation.
- Shell `|| true` / `|| return 0` after a command that can fail several ways is Critical unless the suppressed error is intentional and enumerated.
- A file referenced by the PR must be committed (`git ls-files`), not just present locally.
- When you flag a pattern, grep the codebase for other occurrences and include them.
- If a concern doesn't apply now (e.g. code commented out), surface it with a suggested TODO rather than dismissing it.
- After listing findings, re-read the diff for cascades: checklists, examples, version pins repeated elsewhere.
- Changes to agent instructions, settings, or permission files: flag unsafe loosening or escalation as Critical.
- Skill files: instructions an agent can't act on ("ask in #channel") should become "surface to the user and stop".
- Comment only on lines the PR changed.

### 4. Tests

Run the repo's tests for the changed code and report pass/fail with output; note whether failures are pre-existing. For infra-as-code, cite the CI plan output instead of planning locally. Check claimed manual tests, run the gaps you can, and propose exact commands for the rest. If evidence comes from a CI build, confirm it ran on (or near) the current HEAD.

### 5. Final output

Severity: **Critical** (must fix), **Suggestion** (consider), **NIT** (low priority).

Present findings grouped by severity, plus a "not worth raising" list with reasons, and let the user adjust before drafting.

Calibration:
- A change that guarantees a break elsewhere in the same repo is Critical and belongs in the same PR.
- An inconsistency with a clear codebase pattern is a Suggestion even if both approaches work.
- Unchecked hard prerequisites in a "Don't merge" section are Critical; recommend draft status.
- Replacing a legacy tool: compare real output; raise parity gaps only with a breaking consumer you can cite. Dropped safety checks and performance regressions are Critical.

Don't mention: stdlib behavior, standard idioms, harmless defensive code, micro-optimizations off hot paths, extra tests for an already-covered branch, sanitization of trusted internal inputs, findings the author already consciously rejected, stale bot findings on files no longer in the diff.

Writing:
- Informal and question-led; no preamble. Prefer questions over assertions where the author owns the domain. Inline comments 2-4 sentences.
- Bug-fix suggestions include a concrete diff or snippet.
- Version recommendations say why not each alternative.
- Near-merge PRs: open with a brief positive assessment and frame remaining items as advisory.
- With no Critical findings, recommend approving with Suggestions and NITs as optional follow-ups.
- Approvals include the commands run and key output, never a bare "LGTM".
- Only findings introduced or perpetuated by the PR go in the review; pre-existing security issues go in a separate tracking issue.

## Write operations

- Default: output review text in chat for the user to post.
- Post, approve, request changes, resolve threads, or dismiss reviews only after an explicit yes to a specific question ("Post this review to owner/repo#N?"). Never merge.
- A review is `POST repos/<o>/<r>/pulls/<n>/reviews` (`event=COMMENT|APPROVE|REQUEST_CHANGES`), not an issue comment. Check for your own pending review first; one pending review per PR is allowed.
- Inline comments via `POST .../pulls/N/reviews` need `path` + `position` (1-indexed diff position, cumulative across hunks; the `@@` header is position 1). `line` + `side` return 422 there. Build the JSON in a file and pass `gh api --input <file>`.
- Pending review comments are only reachable under `pulls/<n>/reviews/<id>/comments` and editable only via GraphQL (`updatePullRequestReviewComment`).
- Submitted reviews can't be deleted, but their body can be edited (`PUT pulls/<n>/reviews/<id>`).
- If an earlier CHANGES_REQUESTED review of yours is now moot, offer to dismiss it.
- Verify by re-fetching the posted review.

## Parallel batch triage (multiple PRs)

### 1. Parse and filter

Accept `owner/repo#N`, URLs, or `#N` with remote inference. When discovering via `review-requested:@me`, paginate until `hasNextPage` is false. Skip and report drafts, closed/merged PRs, PRs you already reviewed, and PRs you authored.

### 2. Dispatch

One subagent per PR, each running the single-PR review and returning the report below. Subagents post nothing. If a subagent fails on permissions, retry sequentially.

```
PR: owner/repo#123
Author: @handle
Type: feature | fix | cleanup | chore
Verdict: Looks OK | Needs changes | Needs more looking
Findings:
  Critical: <bullets or "none">
  Suggestions: <bullets or "none">
  NITs: <bullets or "none">
  Improvements: <optional, beyond the diff>
Tests: passed | failed | skipped | n/a
```

On error: `PR`, `Error: <reason>`, `Verdict: Error`.

Before any verdict, a subagent must have fetched inline comments, verified CI claims against actual logs, and ranked blocking dependencies first.

### 3. Summary table

```
| PR                            | Author   | Verdict       | Critical | Suggestions | NITs |
|-------------------------------|----------|---------------|----------|-------------|------|
| [owner/repo#123](https://...) | @author1 | Looks OK      | —        | 1           | 2    |
| [owner/repo#456](https://...) | @author2 | Needs changes | 2        | 0           | 1    |
```

Then findings per PR (Critical, Suggestions, NITs, Improvements).

### 4. Decisions and posting

Accept blanket or per-PR decisions: `approve`, `request-changes <reason>`, `comment <text>`, `skip`. Post nothing without an explicit decision, then post per the write-operation rules.

## Capture learnings

At the end of a session, if the user corrected the approach, append the corrected rule to `## Learnings` below in one sentence with a short rationale.

## Learnings

- When the user links a posted review or comment, fetch it right away; they may have changed the draft.
- If the PR author has left the project, don't ask them for follow-ups: sort each finding into "drop", "fold into the next change touching this code", or "tracking issue", and check proposed deadlines against the team's planning.
