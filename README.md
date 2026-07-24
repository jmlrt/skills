# Agent skills

Opinionated, public workflows for Claude Code, Codex, and Cursor. They cover repeatable tool use and review processes; project, company, account, and machine-specific rules belong in local guidance.

## Compatibility

Every skill uses the portable `name` and `description` metadata required by Codex. Some skills also include Claude Code `allowed-tools` metadata; other agents can ignore it.

- **Codex**: install or symlink selected skill folders under `~/.agents/skills/`, or a repository's `.agents/skills/`.
- **Claude Code**: install with your preferred skill manager, or place selected folders under its skills directory.
- **Cursor**: supports `SKILL.md` Agent Skills in its editor and CLI. Use its skill installation flow for placement; vendor-specific metadata can be ignored.

Keep only the skills you use installed. Their descriptions are always loaded for discovery, so a smaller, focused set produces better matching.

## Skills

| Skill | Purpose | Optional dependency |
| --- | --- | --- |
| `github` | `gh` CLI reads, writes, reviews, workflows, and troubleshooting. | `gh` |
| `pull-request` | Author a focused pull request and address review feedback. | `git`, `gh` |
| `review-pull-request` | Independently review one or more pull requests. | `git`, `gh` |
| `triage-dependency-prs` | Classify dependency and backport PRs as close, rebase, order, stale, or ready for review. | `gh` |
| `jira` | Retrieve Jira work-item context through `acli`. | `acli` |
| `buildkite` | Trigger and investigate Buildkite builds through `bk`. | `bk` |
| `python-development` | Apply concise Python implementation and review defaults. | — |
| `golang-development` | Apply concise Go implementation and review defaults. | — |
| `plan-with-review` | Produce an implementation plan and a separate QA pass. | — |
| `optimize-workspace-context` | Simplify and improve `AGENTS.md` or `CLAUDE.md`. | — |
| `review-claude-config` | Audit Claude guidance and memory files. | — |
| `review-claude-settings` | Audit Claude Code permission settings. | — |
| `englog-cli` | Read or update an Englog daily journal, including session capture. | `englog` |
| `session-learnings` | Persist recurring session corrections in the narrowest useful guidance. | — |

## Principles

- Default to read-only access for external systems; require an explicit request before writes.
- Verify unstable CLI behavior against the installed version rather than treating a local workaround as universal.
- Keep public skills free of organization names, personal paths, credentials, internal URLs, and account-specific policy.
- Prefer repository-local guidance for repository conventions and private global guidance for personal workflow.

## Contributing

Read [SKILLS_STANDARD.md](SKILLS_STANDARD.md) before changing or adding a skill. Validate the frontmatter and re-read the changed workflow; do not add generic coding advice that a capable agent already knows.
