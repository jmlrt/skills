---
name: review-claude-config
description: Audit the ecosystem of Claude config files — global CLAUDE.md, per-repo CLAUDE.md and CLAUDE.local.md, memory files, and skills — for redundancy, inconsistency, outdated facts, and misplaced content. Use when asked to "review CLAUDE.md", "audit claude config", "clean up claude files", or "check what should be global vs local".
allowed-tools: Read, Glob, Bash(find:*), Bash(grep:*), Edit, Write
---

# Review Claude Config

Audits the full ecosystem of Claude config files and produces a structured findings report. Changes require explicit confirmation before applying.

## Scope

1. **Global**: `~/.claude/CLAUDE.md`
2. **Per-repo**: `CLAUDE.md` and `CLAUDE.local.md` under the user-provided workspace root (all depths)
3. **Memory**: `~/.claude/projects/<project>/memory/` (index + files)
4. **Skills**: `~/.claude/skills/*/SKILL.md`

---

## Phase 1: Discovery

Run these in parallel:

```bash
find <workspace-root> -maxdepth 4 \( -name "CLAUDE.md" -o -name "CLAUDE.local.md" \) 2>/dev/null | sort
```

```bash
ls ~/.claude/skills/
```

Then read in parallel:
- `~/.claude/CLAUDE.md` (global config)
- `~/.claude/projects/<project>/memory/MEMORY.md` (memory index, if it exists)
- Each discovered repo `CLAUDE.md` and `CLAUDE.local.md`

---

## Phase 2: Audit Global CLAUDE.md

Check for:

**Redundancy** — same fact stated twice across sections. Decision: keep the more specific instance, remove or collapse the other.

**Internal inconsistency** — conflicting facts within the file (e.g. one section says "use X" and another says "use Y for the same case").

**Outdated facts** — tools, workflows, or systems that no longer apply. Red flags: tool names not in the active Tooling table, processes that contradict the CI/Workflow section, dates that have passed.

**Bloat** — content generic enough to belong in a skill file, or specific enough to belong in a per-repo CLAUDE.local.md. Global rules should apply across all repos. Repo-specific conventions (commit format, nav file, link syntax) belong locally.

**Missing facts from memory/skills** — if a memory file or skill contains a rule the user would expect the global CLAUDE.md to enforce, flag it for promotion.

---

## Phase 3: Audit Per-Repo Files

For each repo's `CLAUDE.md` / `CLAUDE.local.md`:

**Should be global** — a rule applies to all repos, not just this one (e.g. a git convention, a tool flag, a security rule). Flag for promotion to `~/.claude/CLAUDE.md`.

**Duplicates global** — a rule already covered verbatim by the global file. Flag for removal from the repo file (avoid drift).

**Outdated** — references to tools, branches, or processes that no longer exist in this repo.

**Cross-repo inconsistency** — two repos have conflicting guidance for the same concept (e.g. different commit message formats). Flag; do not silently resolve.

---

## Phase 4: Memory and Skills Cross-Check

**Memory → Global CLAUDE.md**: A memory file records a fact or user preference that should be a standing rule (not ephemeral state). Flag for promotion. Criteria: would the user expect this to apply in every future session, not just the one where it was learned?

**Skills → Global CLAUDE.md**: A skill documents a tool-specific workflow detail that should instead be a global policy (e.g. "always confirm before posting to GitHub"). Conversely, if global CLAUDE.md restates what a skill already covers fully, the global entry is redundant.

---

## Phase 5: Report

Present findings as a structured table before any changes. Group by severity:

```
## Findings

### Global CLAUDE.md
| # | Category       | Section         | Issue                              | Proposed fix              |
|---|---------------|-----------------|-------------------------------------|---------------------------|
| 1 | Redundancy    | Tooling / Git   | GPG signing stated twice            | Remove from Tooling table |
| 2 | Inconsistency | CI / Tooling    | gh described as CI tool             | Update gh description     |
| 3 | Outdated      | CI / Workflow   | Deprecated process still mentioned  | Update the workflow guidance |

### Per-Repo Files
| # | File                      | Category        | Issue                              | Proposed fix              |
|---|--------------------------|-----------------|-------------------------------------|---------------------------|
| 1 | repo/CLAUDE.md            | Should be global | Commit format rule                 | Move to global CLAUDE.md  |

### Memory / Skills
| # | Source                    | Issue                              | Proposed fix              |
|---|--------------------------|-------------------------------------|---------------------------|
| 1 | memory/feedback_*.md      | Preference not reflected globally  | Add rule to global CLAUDE.md |
```

If no findings in a category, state "No findings."

---

## Phase 6: Apply (with confirmation)

After presenting the report, ask: **"Apply all? Or specify which numbers to apply."**

- Apply only the confirmed items.
- For global CLAUDE.md edits: use targeted `Edit` calls (one per finding); do not rewrite entire sections.
- For repo file edits: same — targeted edits only.
- For memory/skill promotions: add the rule to the appropriate section in global CLAUDE.md; do not delete the source unless it is truly redundant.
- Re-read each edited section after applying to confirm the change landed correctly.

---

## Constraints

- Never rewrite an entire file unless the user explicitly asks.
- Never silently resolve cross-repo inconsistencies — always present both versions and ask which wins.
- Do not promote repo-specific content to global just because it appears in multiple repos; check whether it is genuinely universal first.
- Line length ≤120 characters in CLAUDE.md files.
