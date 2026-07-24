# Skill authoring standard

Skills in this repository are public, concise, and useful to both Claude Code and Codex. They add workflow knowledge that an agent is unlikely to infer reliably; they do not reproduce general programming knowledge or private operating context.

## Required metadata

Every `SKILL.md` starts with:

```yaml
---
name: skill-name
description: Concise scope and trigger language. Use when...
---
```

- `name` is lowercase kebab-case and matches the directory name.
- `description` starts with the main use case and includes clear trigger terms. Keep it concise: skill descriptions are loaded for every session.
- Additional frontmatter must be platform-specific and optional. For example, Claude Code may use `allowed-tools`; Codex-specific presentation or invocation metadata belongs in `agents/openai.yaml` when needed.

## Design rules

- One skill, one coherent workflow or tool domain.
- Keep `SKILL.md` under 500 lines; use one-level-deep references only for detailed material that is loaded conditionally.
- Write the minimum instruction needed to make an agent reliably better. Assume the agent already understands normal coding, Markdown, shell, and Git fundamentals.
- Use a precise recipe for fragile or destructive operations; use principles when context determines the right choice.
- State defaults and exceptions, not exhaustive possibilities.
- Default external actions to read-only and require explicit user intent for writes.

## Public-release checks

Before publishing, remove or generalize:

- Names of people, companies, teams, repositories, services, channels, and internal URLs.
- Local paths, machine setup, personal preferences, account details, credentials, and permission-workaround lore.
- Claims tied to a specific CLI version, sandbox, organization configuration, or outage. State how to verify instead.

Put those details in private global guidance or repository-local instructions.

## Structure

Use a short title, then task-oriented sections. Keep headings no deeper than H3. Supporting files must be linked from `SKILL.md` with a sentence explaining when to read them.

For skills that write external state, include:

1. The confirmation boundary.
2. The smallest safe action.
3. A verification step.

## Maintenance

- Re-read the edited workflow and validate its frontmatter.
- Update the README when adding, removing, or renaming a skill.
- If a rule is specific to one user, machine, organization, or repository, move it out of this repository rather than adding an exception here.
