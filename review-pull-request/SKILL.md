---
name: review-pull-request
description: "Review pull requests as a reviewer. Use when validating a PR before merge: performs independent code review, runs tests, validates manual testing. Handles single PRs with detailed analysis or multiple PRs in parallel batch mode with summary triage table."
allowed-tools: "Bash(git:*), Bash(gh:*), Bash(grep:*), Bash(make:*), Read, Glob"
argument-hint: [owner/repo#number, PR URL, or multiple]
---

# PR Review (Reviewer)

This skill reviews pull requests as a reviewer. Authors use the **pull-request** skill to create and update PRs, then request review.

## Single vs. Multiple PRs

**Single PR**: Provide one `owner/repo#123` or PR URL → Full detailed review (7 phases).

**Multiple PRs**: Provide list like `owner/repo#123 owner/repo#456` or `owner/repo#123, owner/repo#456` → Parallel batch triage (phases below).

---

## Review stance

Default to **polish mode** (thorough review). User can request **ship-it mode** (pragmatic) or **KISS mode** at any time.

### Polish mode (default)
- Request NIT fixes in-PR via inline comments
- Suggest refactoring, ask for more tests, give per-file detailed feedback
- Consolidate findings into a detailed summary comment

### Ship-it mode (pragmatic)
- Focus on critical/blocking issues only
- Consolidate all NITs into one "optional follow-up" list at end of review
- No change requests for style, naming, or minor refactoring
- Bias toward approval with conditions

### KISS/YAGNI mode
- After standard correctness review, apply a second pass asking: "is this the simplest correct solution?"
- Flag: unnecessary abstractions, over-documented internals, YAGNI additions, maps/structs where booleans/scalars suffice, capacity hints in non-hot paths
- Cross-reference with "What NOT to mention" — KISS findings that are harmless should still be dropped

**How to request**: Say "urgent" / "pragmatic" / "focus on critical" / "skip NITs" for ship-it. Say "KISS" / "YAGNI" / "simplify" / "keep me honest" for KISS mode.


---

## Single PR Review Checklist

Work through all phases. Phases 1–2 can run in parallel using batch tool calls.

### Pre-flight: author check

Before starting, confirm the requester is not the PR author. GitHub does not allow authors to approve their own PRs:

```bash
gh pr view <n> --repo <owner>/<repo> --json author | jq -r '.author.login'
# compare against: gh api user | jq -r '.login'
```

If the requester IS the author: surface this immediately — they need an external reviewer, not a self-review. Offer to help request review from someone (`gh pr edit <n> --add-reviewer <login>`). Do not proceed with a full code review only to flag the blocker at the end.

---

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

Check repository agent instructions (such as `AGENTS.md` or `CLAUDE.md`) for a `## PR Review` section with repo-specific checks. Apply those checks alongside this generic checklist.

**Documentation pattern check**: read the repo's `README.md` and agent instructions (if present) and check whether the PR should have updated them. Specifically: if the PR adds a CLI command, new feature, or new workflow, check whether prior PRs in the same area included README or agent-instruction updates (`git log --oneline -5 -- README.md AGENTS.md CLAUDE.md`). Flag any missing documentation as a Suggestion in Phase 7.

**Cross-repo impact** (pipelines, scripts, configs referenced by the PR): check for a local clone before fetching via `gh api`. Local reads are faster and work offline.

### Phase 2: Comment triage

For each existing review comment thread (including outdated):
- Check if the issue is addressed in the latest diff
- Classify: `can resolve` (addressed or correctly dismissed) vs `still needs fix`

Present the triage list to the user before taking any action. Only resolve threads after explicit user approval. Use the **github** skill's resolve-thread command.

### Phase 3: Independent code review

**Before analyzing concerns on modified files**: `gh pr diff` hunk headers show the OLD file's enclosing function name as context — this can be misleading when the PR branch has significantly restructured the function (changed signature, commented out code, etc.). For files with substantive modifications, Read the actual PR branch file from the worktree to see the full current state before raising concerns.

**Future-proofing concerns**: if a concern doesn't apply to the current PR state (e.g., a dependency-ordering issue where the relevant code is commented out), do not dismiss it as moot — surface it explicitly with a suggestion to add a code-level TODO so whoever re-enables/restores the code can't miss it.

Review the diff for:
- **Correctness**: logic bugs, edge cases, off-by-one errors
- **Error handling**: swallowed errors (`if err == nil { use(result) }` pattern), missing validation, silent failures. In shell scripts specifically: `|| return 0` / `|| true` after a command that can fail for multiple reasons is a Critical flag — it silently converts any failure (network error, auth failure, wrong credentials, etc.) into a success with empty output. It's only safe when the error is *intentional and exhaustively enumerated* (e.g., only 404 is expected and handled separately). Flag this as Critical and ask whether the intent is to suppress all errors or only a specific one.
- **Tests**: coverage of new/changed behavior, missing edge cases
- **Consistency**: patterns matching the rest of the codebase, DRY violations, duplicate code blocks
- **Security**: secrets handling, permissions, injection vectors
- **Maintainability**: readability, naming clarity, complexity — would a newcomer understand this code in 6 months?
- **Documentation**: New or non-trivial functions have comments or docstrings; new pipelines/automation/features are documented.
- **Logging / observability**: Logs show *what* was checked (e.g. URLs tested, entities validated, counts), not only high-level "X OK".
- **Scope / design**: For scheduled jobs or broad scope, consider asking whether frequency/scope is necessary.
- **Process / sustainability**: For validation automation, consider whether there is a documented way to keep it in sync as the codebase grows.
- **Security / permissions**: Review changes to `AGENTS.md`, `CLAUDE.md`, settings, or permission files carefully. Flag only an unsafe loosening of restrictions or permission escalation as Critical.
- **Cross-codebase patterns**: If you flag a pattern issue (e.g., broad exception handler, missing validation), grep the full codebase for the same pattern. Include findings in your review comment to help the author fix all occurrences, not just the flagged line

Inline comment placement rule: comment only on lines **actually changed by the PR**, not on unchanged context lines visible in the diff hunk.

**Self-filter before presenting findings**: Before surfacing findings to the user, apply the "What NOT to mention" list (see Phase 7). Drop anything that is: stdlib behaviour, an idiomatic pattern (see golang-development patterns), harmless defensive code, a micro-optimisation in a non-hot path, or a missing test for an already-covered code path. Present only what survives the filter.

### Phase 4: Test execution

Run unit tests for the changed code. Use the repo's test runner (check repository agent instructions). Report pass/fail with output. If tests fail, investigate and note whether it is a pre-existing failure or introduced by this PR.

### Phase 5: Manual test assessment

- Review what manual tests are claimed in the PR description and comments
- Identify gaps; if they can be filled without the PR author, do it — run them locally and capture the output
- Propose any remaining manual tests with exact commands

**Test build staleness check**: when the PR description links a CI build as evidence, verify the build ran on (or close to) the current HEAD — `gh api repos/<owner>/<repo>/compare/<build-commit>...<branch> --jq '.commits[].commit.message'`. If commits landed after the test that rename files, change command paths, or bump tool versions, flag that a re-test is needed on the current HEAD before merging.

**When approving**: include the commands run and their key output in the approval comment as evidence. Don't approve with just "LGTM" — show what was tested.

### Phase 6: Issue alignment

If a GitHub issue is linked in the PR body or description:
- Fetch it with `gh issue view <n> --repo <owner>/<repo> --json title,body,comments`
- Compare PR changes against the issue's scope, acceptance criteria, and Definition of Done
- Flag any requirements not covered by the PR — missing features, missing tests, missing CLI entry points, etc.

### Phase 7: Final output

**Severity labels**:
- **Critical** (must fix before merge)
- **Suggestion** (consider fixing)
- **NIT** (nice to have, low priority)

When listing NITs, consider: function comments/docstrings, unit tests for new logic, logging that shows what was checked, documentation for new pipelines/features, and a process to keep validation in sync.

**What NOT to mention** — drop these entirely, they add noise without value:
- Standard library behavior (e.g. `filepath.Walk` recursion, `os.ReadDir` ordering) — trust stdlib
- Idiomatic patterns that look clever but are standard (see golang-development/patterns.md#standard-idioms)
- Harmless defensive code (e.g. skipping file extensions that don't exist in the current tree)
- Micro-optimisations in non-hot paths (e.g. map capacity hints on single-use validators)
- Missing tests for the same code path already covered by an existing test (different input, same branch)
- Input sanitisation for internal packages called from controlled environments (CI pipelines, CLI args)
- **Removed diagnostic/observability code** when a tool is being replaced: before flagging dropped logging (checksums, file listings, etc.), read the replacement tool's own log output to see if it already provides equivalent visibility. Only flag if genuinely missing.
- **Findings already raised by another reviewer and consciously rejected by the author** — check Phase 2 comment triage; if Copilot/another reviewer raised it and the author explicitly dismissed it, do not re-raise it. Re-raising is noise and cannot be undone once posted.

**Ship-it mode output**: single review comment with critical items, followed by one consolidated "optional follow-up NITs" block. No separate inline comments for NITs.

**Polish mode output**: inline comments per finding, plus a summary comment.

**Default**: output the review text in chat for the user to copy-paste via the GitHub UI. Only post directly via `gh pr review` or `gh api` if the user explicitly asks.

**Tone**: informal and question-led. Lead with the question or observation, no preamble. Don't restate what the code does before asking. Don't cite spec documents or Definition of Done in inline comments — the author knows the spec; just ask the question. Empathetic, not prescriptive.

**Near-merge reviews**: when the PR is substantively correct and only minor items remain, open the summary with a brief positive assessment and frame the remaining items as advisory. The repository owners make the merge decision.

**Fix suggestions must include code**: when suggesting a bug fix, show a concrete `diff` or replacement snippet — never describe the change abstractly ("decouple X from Y", "use the right path here"). Abstract descriptions are unclear to the author and hard to act on. If the fix is non-trivial to write out, show the key lines that change and explain why.

**Version recommendations**: when recommending one version over alternatives, always include explicit "why not X, why not Y" rationale for each rejected option. Stating only the recommendation leaves the author unable to evaluate the tradeoff.


## Write operations

- **Resolving threads**: only after user approves the Phase 2 triage list. Never resolve pre-emptively.
- **Posting review**: output review text in chat by default. If user says "post the review" or "submit review", ask confirmation: **"Post review via `gh pr review`? (yes/no)"** — only call `gh pr review` or `gh api` after explicit yes.
- **Approval comment content**: always include the local tests that were run and their key output — commands, what was verified, and the result. Don't post a bare "LGTM".
- **No merging**: never merge a PR via CLI unless explicitly asked.
- **Posting inline comments via REST API**: `gh api repos/.../pulls/N/reviews` requires `position` (integer diff position) for inline comments — NOT `line` + `side` (those fields don't exist on `DraftPullRequestReviewComment` and return 422). Diff position is 1-indexed and cumulative across all hunks: position 1 = the hunk header line (`@@...@@`), position 2 = the first content line, etc. For new files (`@@ -0,0 +1,N @@`): position = file_line_number + 1. Use the Write tool to create a JSON file in the scratchpad, then `gh api --input <path>` — nested `-F "comments[][key]=val"` flags are unreliable for complex bodies.
- **Pending review conflict**: `gh pr review --comment` fails with "User can only have one pending review per pull request" if a draft review exists. Fix: submit the pending review with the new body via `gh api --method POST repos/<owner>/<repo>/pulls/<n>/reviews/<id>/events -f event=COMMENT -f body="..."`. Find the pending review id with `gh api repos/<owner>/<repo>/pulls/<n>/reviews | jq '.[] | select(.user.login == "<login>" and .state == "PENDING") | .id'`.
- **Submitted reviews cannot be deleted**: `DELETE /pulls/<n>/reviews/<id>` returns 422 "Can not delete a non-pending pull request review". Once posted, a review is permanent — there is no API to undo it. Think before posting; if a redundant comment was already sent, note it to the user and move on.


## Backport rules

Detect backport: check if `labels` contains `backport` (fetch via `gh pr view <n> --repo <r> --json labels`).

For backport PRs:
1. **Fetch the source PR** from the backport body (look for the linked PR on `main`, e.g. `[Title (#NNN)](url)`) and diff it: `gh pr diff <source-pr> --repo <r>`
2. **Verify consistency**: the backport diff must match the source PR diff (modulo branch-specific context lines). Flag any additions, omissions, or divergences.
3. **Only flag issues that are new in the backport** — divergences from the source, merge conflicts, wrong branch assumptions, or stale TODOs referencing unmerged PRs.
4. **Do not flag issues also present in the source PR on main** — those are already accepted and must not be re-raised in the backport.


# Parallel Triage Mode (Multiple PRs)

When reviewing multiple PRs, orchestrate in parallel.

## Phase 1: Parse and validate

Parse PR inputs (handles `owner/repo#123`, `https://github.com/owner/repo/pull/123`, bare `#123` with git remote inference).

**If discovering PRs via `review-requested:@me` search**: paginate through all results using `first: 50` + cursor loop (`pageInfo { hasNextPage endCursor }`) until `hasNextPage: false`. Do not use `first: 20` — there can be 100+ matching PRs and a low limit silently drops most. Note: GitHub search index has gaps; some PRs may not appear even when the user is a confirmed direct reviewer — cross-reference with the user if they report missing PRs.

Validate each PR with `gh pr view <n> --repo owner/repo --json number,title,author,url,isDraft,state` (or by passing the full PR URL).

**Pre-flight filter** — before dispatching subagents, check each PR and skip (inform user):
- `isDraft: true` → not ready for review yet
- `state: CLOSED` or `state: MERGED` → already resolved
- Reviewer has already submitted a review (`gh api repos/.../pulls/N/reviews | jq '[.[] | select(.user.login == "USERNAME")]'`)

Present the skipped list to the user before proceeding with the remaining PRs.

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
