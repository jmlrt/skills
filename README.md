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
| `github` | Read GitHub issues/PRs/repos using the `gh` CLI. Read-only by default. | `gh` CLI |
| `create-pull-request` | Create and update GitHub pull requests with opinionated title/body conventions. | `gh` CLI |
| `review-pull-request` | Comprehensive PR review: triage comments, code review, test execution, Jira alignment. | `gh` CLI; `jira` skill (optional) |
| `triage-pull-requests` | Batch-review multiple PRs in parallel. Produces a triage table, then posts reviews on decision. | `gh` CLI; `review-pull-request` skill |
| `jira` | Read Jira tickets and epics using the Atlassian CLI (`acli`). Requires `{JIRA_BASE_URL}` configured. | `acli` CLI |
| `buildkite` | Trigger and inspect Buildkite builds using the `bk` CLI. | `bk` CLI |

### Skill dependencies

- `review-pull-request` uses the `github` skill for all `gh` reads and the `jira` skill for ticket context (graceful fallback if not installed).
- `triage-pull-requests` uses `review-pull-request` for review logic and `github` for posting.

## Configuration

### Jira base URL

The `jira` skill uses `{JIRA_BASE_URL}` as a placeholder. Set your instance URL in your workspace `CLAUDE.md` or `AGENTS.md`:

```markdown
## Jira configuration
JIRA_BASE_URL=https://yourorg.atlassian.net
```

## Local dev workflow

```bash
# Clone repo
git clone git@github.com:jmlrt/skills.git ~/Code/jmlrt/skills/

# Create direct symlinks into ~/.claude/skills/ (edits are picked up immediately)
for skill in github create-pull-request review-pull-request triage-pull-requests jira buildkite; do
  ln -sf ~/Code/jmlrt/skills/$skill ~/.claude/skills/$skill
done
```

After that, editing any `SKILL.md` file takes effect immediately — no reinstall needed.

> **Note**: `npx skills add -g ./` copies files to `~/.agents/skills/` rather than symlinking to the repo, so edits are not picked up automatically. Use the manual symlink approach above for local development.

### Update

```bash
npx skills update          # update all installed skills
npx skills check           # check for updates without installing
```
