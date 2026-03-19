# skills

Personal agent skills for Claude Code and Cursor — GitHub, Jira, Buildkite, and PR workflows.

## Compatibility

| Tool | Supported |
|---|---|
| Claude Code | Yes |
| Cursor | Yes |

## Install

```bash
# Install all skills globally (into ~/.claude/skills/)
npx skills add -g jmlrt/skills

# Install into the current project only
npx skills add jmlrt/skills

# Selective install
npx skills add -g jmlrt/skills --skill github --skill review-pull-request
```

## Skills

| Skill | Description | Optional deps |
|---|---|---|
| `github` | Manage GitHub issues/PRs/repos using the `gh` CLI. Retrieve context, create/edit issues and PRs, manage workflows, resolve review threads. | `gh` CLI |
| `pull-request` | Guide pull requests through their complete lifecycle (create → iterate → validate). Covers PR templates, title/body conventions, file validation, review feedback iteration, merge readiness checks. | `gh` CLI |
| `review-pull-request` | Comprehensive PR review: triage comments, code review, test execution, Jira alignment. Includes CLAUDE.md safety checks and cross-codebase pattern scanning. | `gh` CLI; `jira` skill (optional) |
| `python-development` | Production patterns for modern Python development: uv, ruff, ty, make, pre-commit. Type safety, separation of concerns, error handling, test organization. | None (reference only) |
| `triage-pull-requests` | Batch-review multiple PRs in parallel. Produces a triage table, then posts reviews on decision. | `gh` CLI; `review-pull-request` skill |
| `jira` | Read Jira tickets and epics using the Atlassian CLI (`acli`). Requires `{JIRA_BASE_URL}` configured. | `acli` CLI |
| `buildkite` | Trigger and inspect Buildkite builds using the `bk` CLI. | `bk` CLI |

### Skill dependencies

- `pull-request` uses the `github` skill for all `gh` CLI operations.
- `review-pull-request` uses the `github` skill for all `gh` reads and the `jira` skill for ticket context (graceful fallback if not installed).
- `triage-pull-requests` uses `review-pull-request` for review logic and `github` for posting.
- `python-development` is a reference skill (no external dependencies).

## Configuration

### Jira base URL

The `jira` skill uses `{JIRA_BASE_URL}` as a placeholder. Set your instance URL in your workspace `CLAUDE.md` or `AGENTS.md`:

```markdown
## Jira configuration
JIRA_BASE_URL=https://yourorg.atlassian.net
```

## Local dev workflow

```bash
# Clone and install as symlinks (edits are picked up immediately)
git clone git@github.com:jmlrt/skills.git ~/Code/jmlrt/skills/
cd ~/Code/jmlrt/skills/
npx skills add -g ./
```

After that, editing any `SKILL.md` file takes effect immediately — no reinstall needed.

### Update

```bash
npx skills update          # update all installed skills
npx skills check           # check for updates without installing
```
