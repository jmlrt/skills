# Repository guidance

Skills here are public and must follow `SKILLS_STANDARD.md`. Read it before creating, updating, or reviewing a skill — it is the source of truth. The points below are the enforcement checklist; keep this file to enforcement points and put detailed rules in the standard, not here.

## Creating or updating a skill

- `SKILL.md` frontmatter: `name` in lowercase kebab-case matching its directory, plus a concise `description` with trigger terms. Platform-specific extras stay optional.
- Keep `SKILL.md` under 500 lines, headings no deeper than H3, and supporting files one level deep, each linked from `SKILL.md` with a sentence saying when to read it.
- Public-release scrub: no names of people, teams, or orgs; no local paths, machine setup, credentials, or permission-workaround lore; no claims tied to a specific CLI version or configuration — generalize and say how to verify. User- or repo-specific rules do not belong in this repository.
- A skill that writes external state must state its confirmation boundary, the smallest safe action, and a verification step.
- Adding, removing, or renaming a skill requires a matching `README.md` update.
- Run `python3 scripts/validate_skills.py` and re-read the changed workflow end to end before committing.

## Reviewing a PR that touches skills

Apply the same checklist to every changed `SKILL.md` and reject anything that leaks private context or only works in one CLI (skills must stay portable across Vibe, Claude Code, and Codex).
