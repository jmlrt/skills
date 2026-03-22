---
name: buildkite
description: "Interact with Buildkite using the bk CLI. Use when the user wants to trigger builds, check build status, list pipelines, view build logs, or perform any Buildkite operations from the command line."
allowed-tools: "Bash(bk:*), Bash(jq:*), Read"
argument-hint: [pipeline-slug or build-number]
disable-model-invocation: true
---

# Buildkite CLI (`bk`)

## Triggering Builds

```bash
bk build create --pipeline <org>/<pipeline> --branch <branch>
bk build create --pipeline <org>/<pipeline> --branch <branch> --commit <sha> --message "..." \
  --env KEY1=value1 --env KEY2=value2
bk build create --pipeline <org>/<pipeline> --branch main --web   # trigger and open in browser
```

**Prompts for confirmation in non-interactive shells** — pipe `Y` explicitly:
```bash
printf 'Y\n' | bk build create --pipeline <org>/<pipeline> --branch <branch> --message "..."
```

**⚠️ Security: Always quote env values** — prevent shell metacharacter injection:
```bash
# ❌ WRONG: unquoted value vulnerable to injection
bk build create --pipeline org/pipe --env KEY=value;rm -rf /

# ✅ CORRECT: quoted to treat as literal string
bk build create --pipeline org/pipe --env "KEY=value;safe"
```

## Querying Build Status

```bash
bk build view                                              # most recent (auto-detects from git)
bk build view <build-number> --pipeline <org>/<pipeline>
bk build list --pipeline <org>/<pipeline>
bk build list --pipeline <org>/<pipeline> --branch <branch> --state failed --since 24h
```

### Build frequency analysis

**Always pass `--no-limit`** — the default cap is 50 results, which covers less than one day for high-frequency pipelines.

**Exclude today** (partial day distorts averages): filter `date < today` when aggregating.

**Low-activity pipelines**: if 0 builds in 3 days, extend to 7 then 10 days before concluding inactive.

**Pipeline 404**: mark explicitly — slugs in docs can be stale/renamed. Don't silently treat as 0 activity.

## Pipeline Operations

```bash
bk pipeline list
bk pipeline view <org>/<pipeline>
```

## Job and Log Operations

There is no `--build` flag for `bk job list` — use `bk build view` and parse the JSON instead.

```bash
bk job log <job-id> -p <org>/<pipeline> -b <build-number>
bk job log <job-id> -p <org>/<pipeline> -b <build-number> --no-timestamps
```

**`bk job log` does NOT support `-o json`.**

**Large logs**: use `head -N` instead of `tail -N` or `grep` — `head` exits early via SIGPIPE and is significantly faster. For pipeline YAML, download the artifact instead:
```bash
bk artifacts list <build-number> --pipeline <org>/<pipeline>
bk artifacts download <artifact-id>
```

**`bk build view -o json` warning prefix**: output starts with a deprecation warning before the JSON. Strip it:
```python
data = json.loads(next(l for l in raw.splitlines() if l.strip().startswith('{')))
```

**Empty log output**: either a trigger step (check the downstream build) or expired logs. Fall back to reading the build script from the local repo or via `gh api`.

## Common Workflows

```bash
bk build rebuild <build-number> --pipeline <org>/<pipeline>
bk build cancel <build-number> --pipeline <org>/<pipeline>
bk build view <build-number> --pipeline <org>/<pipeline> --web
```

## Tips

- Use `-o json` for machine-readable output (`build`, `pipeline` commands; NOT `job log`)
- **Prefer `jq` over Python** for simple parsing: `bk build list -p org/pipeline -o json | jq -r '.[].state'`
- Short flags: `-p` (pipeline), `-b` (branch), `-m` (message), `-c` (commit), `-e` (env), `-w` (web)

## Real-world workflow: Trigger build and monitor

**Goal**: Trigger a build, check status, and inspect logs if failed.

```bash
# 1. Trigger build on current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
BUILD=$(bk build create --pipeline org/my-pipeline --branch $BRANCH --web \
  | jq -r '.id')

echo "Build started: https://buildkite.com/org/my-pipeline/builds/$BUILD"

# 2. Poll status (simple polling, replace with proper wait-for-build if available)
while true; do
  STATUS=$(bk build view $BUILD --pipeline org/my-pipeline -o json | jq -r '.state')
  echo "Status: $STATUS"
  [ "$STATUS" = "passed" ] || [ "$STATUS" = "failed" ] && break
  sleep 5
done

# 3. If failed, download logs
if [ "$STATUS" = "failed" ]; then
  bk build view $BUILD --pipeline org/my-pipeline --log-failed | head -50
fi
```

## Real-world workflow: Check logs of a failed build

**Goal**: Investigate a failed build by retrieving job logs and finding the error.

```bash
# 1. Get the most recent failed build for a pipeline
PIPELINE="org/my-pipeline"
BUILD=$(bk build list --pipeline $PIPELINE --state failed --limit 1 -o json | \
  jq -r '.[0].number')

echo "Checking failed build #$BUILD"

# 2. List all jobs in the build with their status
bk build view $BUILD --pipeline $PIPELINE -o json | \
  jq -r '.jobs[] | "\(.id): \(.name) → \(.state)"'

# 3. Retrieve log for the first failed job
FIRST_JOB=$(bk build view $BUILD --pipeline $PIPELINE -o json | \
  jq -r '.jobs[] | select(.state == "failed") | .id' | head -1)

echo "Retrieving logs for job: $FIRST_JOB"
bk job log $FIRST_JOB --pipeline $PIPELINE --build $BUILD | head -100

# 4. Search logs for error patterns (e.g., "Error", "FAIL", "panic")
echo "--- Error summary ---"
bk job log $FIRST_JOB --pipeline $PIPELINE --build $BUILD | \
  grep -iE "(error|fail|panic|exception)" | head -20
```

**Tips**:
- **Multiple failed jobs**: Loop through `jq -r '.jobs[] | select(.state == "failed") | .id'` to check all failures
- **Large logs**: Use `head -N` to peek at the start, or `grep <pattern>` to find specific errors — avoid `tail -N` which buffers the entire log
- **Specific line range**: `bk job log <id> -p $PIPELINE -b $BUILD | sed -n '50,150p'` to view lines 50–150
- **Web view**: `bk build view <build-number> --pipeline <org>/<pipeline> --web` to open in browser and inspect interactively

## Sandbox / Permissions

**Always use `required_permissions: ["all"]`** — `["network"]` is NOT sufficient: `bk` fails with a TLS certificate error inside the sandbox even with network access enabled.
