---
name: plan-with-review
description: Runs a two-pass planning workflow (draft → Plan QA → final plan + QA notes). Use when the user asks to create a plan, is in plan mode, requests an implementation plan, asks to "review this plan" for issues/missing parts/improvements/clarifications, or mentions planning, missing parts, or clarifications.
---

# Plan with review

When the user asks for a plan (or plan mode is active), run the **two-pass** workflow. Do not present a draft plan without QA; always run the QA pass and then present the final plan plus QA notes.

## Default behavior

- **Trigger**: User asks for a plan, is in plan mode, or says "review this plan" / "missing parts" / "clarifications" in a planning context.
- **Workflow**: Draft plan → run Plan QA (checklist below) → incorporate fixes → present **final plan** then **`## Plan QA notes`**.
- **Always show QA notes**: Do not hide or skip the Plan QA notes section, even when the final plan is concise.
- **Blocking questions**: Use AskQuestion only for true blockers; limit to 1–2 critical questions. Prefer listing assumptions/risks in QA notes over asking unless the answer is required before implementation.

## Preflight (before drafting)

1. **Repo guidance**: look for `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/commands/`, and `.claude/skills/`. Incorporate their constraints; list conflicts or unknowns in Plan QA notes.
2. **Prior art**: search workspace skills/commands and known external tools for patterns that overlap with the problem. Borrow what exists; flag what needs to be built from scratch. Re-inventing something an existing skill, `gh`, or a standard tool already covers is an effort trap.

## Ordering

Run Plan QA **before** presenting the final plan (and before finalizing any plan artifact), so gaps are caught before implementation.

## Plan QA checklist

- Requirements coverage (user intent and constraints)
- Correctness risks / edge cases / failure modes
- Dependencies (internal/external, ordering, unknowns)
- Verification gates (how we’ll know we’re done; include at least one concrete gate)
- Safety/rollback (data loss, irreversible ops, security/privacy; permissions needed)
- **Effort traps** (scope too broad, missing boundaries):
  - Does every component earn its complexity cost? Would removing it lose core value?
  - What do existing tools, libs, or workspace skills already handle that the plan reimplements?
  - YAGNI: is anything built before there is a concrete second use case for it?
  - Unix philosophy: does this do one thing well, or is it several loosely-related tools stitched together?
- **Phase ordering**: does Phase 1 deliver the unique core value on its own (not just scaffold)? Could the user stop after Phase 1 and still get something useful? Are phases ordered by value delivered, not only by technical dependency?
- **Deferred scope**: for large plans, identify items that are genuinely out of scope for the initial implementation. List them in a separate section or companion file so the core plan stays focused and reviewable.
- Repo conventions (file placement, naming, link style, lint/test expectations)

## Output contract

**Final plan**: Scope / constraints / non-goals | Approach (decisions + why) | Files & touchpoints | Step-by-step implementation with verification gates | Test/validation plan | Rollback/safety when applicable.

**Plan QA notes** (section `## Plan QA notes` after the plan):

- **Resolved in QA**: issues incorporated into the final plan
- **Open risks / issues**: remaining risks/unknowns (not blockers)
- **Assumptions made**: for quick user correction
- **Clarifications needed (blockers)**: only 1–2 critical questions before implementation

## Precedence

- If the user explicitly invokes **plan-with-review** (e.g. `/plan-with-review`), always run this two-pass workflow regardless of other instructions (e.g. "be brief").
