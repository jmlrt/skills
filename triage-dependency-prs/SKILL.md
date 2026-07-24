---
name: triage-dependency-prs
description: Triage open dependency/backport/security PRs in a GitHub repo. Identifies redundant, superseded, conflicting, or stale PRs and recommends close, rebase, or merge-ready actions.
---

# Triage Dependency PRs

Scan all open backport, renovate, snyk, and CVE PRs in the repo. Produce a prioritised action table: what to close (superseded), what needs a rebase, what has ordering dependencies, and what is ready to merge — with a merge-confidence rating for each surviving PR.

## Scope

**Repo-scoped, not person-scoped.** This command looks at *all* dep PRs open in a given repo, regardless of who they're assigned to. It answers: "which of these PRs are redundant, conflicting, or ready?" — not "should I approve this PR?"

**What this does NOT do**: review code for correctness, run tests, or post approvals. Use the `review-pull-request` skill for a full review.

**When to run**:
- Periodic repo maintenance: clear the dep PR backlog before it grows unwieldy.
- As a pre-step before a full PR review: if your review queue contains 3+ dependency PRs from the same repo, run this first to close superseded ones before reviewing the survivors.

---

**Target repo**: Use the argument if provided, otherwise detect with `gh repo view --json nameWithOwner -q .nameWithOwner`.

---

## Step 1 — Fetch all relevant open PRs

Run in parallel:

```bash
# All open PRs (up to 150) with full metadata
gh pr list --repo <REPO> --state open --limit 150 \
  --json number,title,labels,headRefName,baseRefName,mergeable,createdAt,updatedAt,files,url
```

Filter to dependency-related PRs: keep any PR where **title or a label** matches `backport`, `renovate`, `snyk`, `CVE`, `Bump.*image`, `update dependency`, `update.*plugin`, or `chore(deps)`.

Group results into two buckets:
- **Branch PRs** (`baseRefName` is not `main`/`master`) — backports
- **Main PRs** (`baseRefName` is `main`/`master`) — renovate, snyk, CVE, and feature PRs with auto-backport labels

---

## Step 2 — Check current state on each target branch

For each unique `(file path, target branch)` pair touched by an open PR, fetch the current file content from the branch HEAD:

```bash
gh api "repos/<REPO>/contents/<PATH>?ref=<BRANCH>" --jq '.content' | base64 -d | grep -i '<dependency>'
```

This lets you compare what the PR proposes vs. what is already on the branch.

---

## Step 3 — Detect redundancy and supersession

Apply these rules:

### Superseded version
Two or more open PRs target the **same file on the same branch** and bump the **same dependency**, but to different versions. The lower-version PR is redundant.

Detection: group by `(target branch, file path)` → find PRs changing the same line (same dep name) to different version strings. Flag the lower-version ones as **CLOSE (superseded by #N)**.

### Exact duplicate
Two PRs make identical changes to the same file on the same branch. Flag as **CLOSE (duplicate of #N)**.

### Already on branch
The dependency in the PR is already at an equal or higher version on the target branch HEAD. Flag as **CLOSE (already at version X on branch)**.

### Merge conflict
`mergeable == "CONFLICTING"`. Flag as **REBASE NEEDED**.

### Ordering dependency (same file, different lines)
Two open PRs touch the same file but different lines (not superseded). Whichever merges second will likely need a trivial rebase. Flag both as **ORDER WITH #N** and recommend merging the more urgent one first.

### Stale
PR has been open > 90 days with no updates in the last 30 days and is still mergeable. Flag as **STALE — review intent**.

---

## Step 4 — Assess merge confidence for surviving PRs

For every PR that is not flagged CLOSE, assess a review-confidence level. This rating answers: "how much additional investigation should happen before normal review?" It never authorizes approval or merge.

**Confidence levels:**

| Level | Meaning | Typical action |
|-------|---------|----------------|
| **very high** | Strong evidence of low regression risk. | Normal review can be brief. |
| **high** | Low risk, but a quick scan of the diff or changelog is worthwhile. | Review normally. |
| **medium** | Non-trivial risk: manual test or targeted code review recommended before merging. | Investigate before merging |
| **low** | Significant risk: breaking changes, no test coverage on affected paths, or unclear impact. | Deep review or hold. |

**Scoring factors — assess all three, then synthesise:**

### Factor A — Bump impact (changelog / release notes)
Fetch the changelog or GitHub releases page for the dependency when possible. Look for:
- `fix` / `patch` release with no API changes → +confidence
- `chore` / `deps` release (transitive dep update only) → +confidence
- New minor features, no removals → neutral
- Deprecation notices or behaviour changes → −confidence
- Breaking changes, API removals, major version bump → −−confidence

### Factor B — Test coverage on affected paths
Grep the repo for how the dependency is imported and which packages use it:
```bash
grep -r '"<dep-import-path>"' --include="*.go" -l   # or equivalent for the language
```
Then check whether those packages have test files (`*_test.go` / `*_test.py` / etc.) and whether CI runs those tests automatically. High test coverage on the affected packages → +confidence.

### Factor C — Criticality of usage in the codebase
Classify how the dependency is used:

| Usage pattern | Impact | Confidence modifier |
|---------------|--------|---------------------|
| Only in `_test.go` files or test helpers | Lowest | +++ |
| Dev tooling only (linter, formatter, code generator, Makefile target) | Very low | ++ |
| Indirect / transitive dependency not directly imported | Low | ++ |
| Utility library used in non-critical paths (logging, metrics, feature flags) | Medium | + |
| Core business logic, main execution path, or API surface | High | − |
| Security-critical path (auth, crypto, network, secrets) | Highest | −− |

**Synthesise:** start from "high", apply modifiers from all three factors, cap the result.

Examples:
- Patch release of a test-only dep with full test coverage → **very high**
- Minor release of a widely-used logging library, no breaking changes, good test coverage → **high**
- Major version bump of a core library touching the main execution path → **low**
- Minor release of a feature-flag library used in business logic, changelog shows no behaviour changes → **medium** (because manual test is prudent for flag evaluation paths)

---

## Step 5 — Output

Present results as a single triage table, sorted by action priority (CLOSE first, then by confidence descending for surviving PRs):

| Action | PR | Branch | Title | Confidence | Reason |
|--------|----|--------|-------|------------|--------|
| **CLOSE** | [#N](url) | branch | title | — | Superseded by [#M](url) (v3.16 > v3.15, same file) |
| **CLOSE** | [#N](url) | branch | title | — | Already at version X on branch |
| **REBASE** | [#N](url) | branch | title | high | Merge conflict; otherwise clean |
| **ORDER WITH [#M](url)** | [#N](url) | branch | title | very high | Both touch file.txt; merge #M first |
| **STALE** | [#N](url) | branch | title | medium | Open 120d, last update 45d ago |
| **READY** | [#N](url) | branch | title | very high | Clean, no conflicts |

After the table, include a short **confidence legend recap** reminding the reader what each level requires (one line each), then list any **close actions to execute** (gh commands). Ask the user to confirm before running them.

---

## Step 6 — Execute closes (with confirmation)

For each PR flagged as CLOSE:
1. State what you are about to do and why.
2. Wait for user confirmation (or proceed if they said "yes, close them all").
3. Run:

```bash
gh pr close <N> --repo <REPO> --comment "<reason — reference the superseding PR number>"
```

Do **not** close PRs flagged REBASE, ORDER, or STALE without explicit user instruction.

---

## Rules

- Never close a PR that is merely stale or has ordering concerns — only close provably superseded or duplicate PRs.
- When in doubt about supersession (e.g., different files, different dependency names), flag as **REVIEW** rather than CLOSE.
- For a Renovate dependency bump, check whether another open PR removes the same dependency. If so, classify the bump as **CLOSE** with the removal PR as its reason.
- For backport PRs: check the version on the **backport branch**, not main — a branch may already have a higher version independently.
- For hermit binary bumps (`bin/.pkg` files + symlink): treat the `.pkg` rename and the symlink update as a single atomic change; a PR that only does one half is incomplete, not superseded.
- Confidence is **never very high** for a major version bump unless the changelog explicitly confirms no breaking changes and the dep is test-only or dev-tooling.
- When you cannot fetch the changelog (private registry, rate limit, etc.), cap confidence at **medium** and note the missing data.
- Never approve or merge as part of triage. Use `review-pull-request` for an independent review and follow the repository's approval policy.
