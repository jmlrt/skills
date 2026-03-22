# Skills Standard

This document standardizes the format for all skills in this repository to ensure consistency, discoverability, and maintainability.

## Frontmatter Format

All skills must have YAML frontmatter with consistent field ordering:

```yaml
---
name: skill-name
description: "One-liner explaining what this skill does and when to use it (200-300 chars)."
allowed-tools: "Bash(tool:*), Read, Write"
argument-hint: [required-arg or optional-arg]
disable-model-invocation: true
user-invocable: false
---
```

### Field Definitions

| Field | Required | Type | Purpose | Notes |
|-------|----------|------|---------|-------|
| `name` | ✅ | string | Skill identifier (lowercase, hyphens) | Used in `/skill-name` invocation |
| `description` | ✅ | string | What the skill does + when to use | 200-300 chars, always quoted, include "Use when" trigger language |
| `allowed-tools` | ⚠️ | string | Tool permissions | Always quoted; use namespace syntax: `Bash(gh:*)` not `Bash` |
| `argument-hint` | ✅ | string | Expected arguments | `[arg]` format, unquoted; leave empty string `""` if none |
| `disable-model-invocation` | ❌ | boolean | Prevent Claude auto-invocation | Set `true` for side-effect skills (push, post reviews, create PRs) |
| `user-invocable` | ❌ | boolean | Hide from `/` menu | Set `false` for reference-only background knowledge |

### Field Ordering

Always use this order:
1. `name`
2. `description`
3. `allowed-tools`
4. `argument-hint`
5. Optional fields (alphabetically: `disable-model-invocation`, `user-invocable`)

---

## Description Format

Descriptions should follow this pattern:

```
[Verb] [object]. [Use/Apply when context]: [what happens]. [Optional: secondary capability].
```

### Examples

✅ **Good:**
- "Create and update pull requests as an author. Use when you're ready to propose changes: creates PRs with comprehensive file validation, tests, commit messages, and PR descriptions."
- "Review pull requests as a reviewer. Use when validating a PR before merge: triages existing comments, performs independent code review, runs tests, validates manual testing."
- "Interact with Buildkite using the bk CLI. Use when the user wants to trigger builds, check build status, list pipelines, view build logs, or perform any Buildkite operations."

❌ **Avoid:**
- "Pull request creation" (vague, no "when")
- "Does stuff with GitHub" (unclear purpose)
- "Manages GitHub issues/PRs/repos using GitHub CLI (gh). Retrieve context, create/edit issues and PRs, manage workflows, and resolve review threads. Use when GitHub issues/PRs are mentioned, when you need details for planning, or when managing PR/issue workflows. This skill is super powerful and can do..." (too long, repetitive)

### Description Length

Target: **200–300 characters**

- Minimum: 150 chars (too short to be discoverable)
- Maximum: 350 chars (too long, loses clarity)
- Ideal: 200–250 chars (clear, searchable, scannable)

---

## Heading Structure

All skills use consistent heading hierarchy: **max depth H1→H2→H3** (no H4+)

### Tool Reference Skills (buildkite, github, jira)

```markdown
# Skill Title: Context

## [Operation Category]

### [Specific Operation or Variant]

**Subheading (bold text, not heading):**
```bash
command
```

### Workflow/Task Skills (pull-request, review-pull-request)

```markdown
# Skill Title: Context

## [Mode/Phase Group]

### Phase N: Action Verb

- Bullet list
- Another point
```

### Rules

- ✅ Use **bold text** (`**text**`) for inline subheadings, NOT headings
- ✅ Use "Phase N:" format (colon, not em-dash: `Phase 1: ` not `Phase 1 —`)
- ❌ Don't put bash comments (`# comment`) inside code blocks as if they're headings
- ❌ Don't use H4+ for organizational structure (use bold text or lists instead)

---

## Supporting Files

If your skill needs more than 500 lines or has multiple distinct areas, use supporting files:

```
my-skill/
├── SKILL.md (250-500 lines: overview + navigation)
├── reference.md (detailed reference material)
├── examples.md (usage examples)
└── scripts/ (optional: utility scripts)
```

### File Naming

- `SKILL.md` — required entry point with overview and navigation
- `reference.md` — detailed API/reference material for reference skills
- `examples.md` — usage examples and common patterns
- `scripts/` — utility scripts or templates (executed, not read)

### Referencing Supporting Files

Add a "Supporting Files" section in SKILL.md to document what's available:

```markdown
## Supporting Files

- **[reference.md](reference.md)** — Complete API documentation
- **[examples.md](examples.md)** — Usage examples with code snippets
- **[templates/](templates/)** — Copy-paste templates for setup
```

---

## Tool Restrictions

Use the `allowed-tools` field to restrict what tools Claude can access without asking:

### Format

Always quote the field value. Use namespace syntax when possible:

```yaml
# Specific subcommands
allowed-tools: "Bash(gh pr*), Bash(gh issue*), Read, Grep"

# Exact permission
allowed-tools: "Bash(bk:*), Bash(jq:*), Read"

# General tools
allowed-tools: "Read, Edit, Write, Grep, Glob"
```

### Principles

- **Narrow scope** — Grant only what the skill needs (don't use wildcards unless necessary)
- **Read-only where possible** — Use `Read, Grep, Glob` for reference skills
- **Tool namespaces** — Specify subcommands when restricting Bash (e.g., `Bash(gh pr*)`)

---

## Side-Effect Skills

Skills that modify state (push code, post reviews, create issues) must set `disable-model-invocation: true`:

```yaml
---
name: create-pr
description: "Create pull requests as an author. Use when..."
disable-model-invocation: true
---
```

**Why:** Prevents Claude from auto-running side-effect operations without explicit user request.

---

## Reference-Only Skills

Skills that provide background knowledge only (not invokable as commands) must set `user-invocable: false`:

```yaml
---
name: python-development
description: "Guide Python development with greenfield defaults..."
user-invocable: false
---
```

**Why:** Prevents the skill from appearing in the `/` menu as an invocable command, while still making it available as background knowledge when Claude needs it.

---

## Checklist for New Skills

- [ ] Frontmatter has all 5 required fields (name, description, allowed-tools, argument-hint, + optional fields)
- [ ] Fields are in correct order (name → description → allowed-tools → argument-hint → optional)
- [ ] Description is 200–300 chars with "Use when" trigger language
- [ ] `allowed-tools` is quoted and uses namespace syntax where applicable
- [ ] `argument-hint` is unquoted (e.g., `[owner/repo#number]` or `""` if none)
- [ ] Headings use max H1→H2→H3 depth
- [ ] No bash comments masquerading as headings in code blocks
- [ ] Phase/step headings use "Phase N:" format (not "Step" or "Phase N —")
- [ ] Supporting files are documented in a "Supporting Files" section
- [ ] Consistent formatting and tone with other skills
- [ ] No unexplained jargon or skill-specific terminology without definition

---

## Examples

### Complete Skill Structure

See any of these skills for examples:
- **Reference skill**: `github/SKILL.md` (tool reference with operations)
- **Task skill**: `pull-request/SKILL.md` (workflow with phases)
- **Complex skill**: `python-development/SKILL.md` (with supporting files)

---

## Maintenance

When updating an existing skill:

1. Keep frontmatter field order consistent
2. Check heading depth (no more than H1→H2→H3)
3. Verify phase/step naming uses colons
4. If adding new sections, check description still fits 200-300 char guideline
5. Update "Supporting Files" section if adding/removing files

---

**Last updated:** 2026-03-22
**Standard version:** 1.0
**Applies to:** All 7 current skills + future skills
