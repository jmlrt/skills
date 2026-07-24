---
name: buildkite
description: "Interact with Buildkite using the bk CLI. Use when the user wants to trigger builds, check build status, list pipelines, view build logs, or perform any Buildkite operations from the command line."
allowed-tools: "Bash(bk:*), Bash(git:*), Bash(grep:*), Bash(sed:*), Bash(jq:*), Read"
argument-hint: [pipeline-slug or build-number]
---

# Buildkite CLI (`bk`)

This skill records practical `bk` workflows. CLI flags and output vary by version and organization configuration; confirm unexpected behavior with `bk <command> --help` before treating a workaround as universal.

## Authentication

Before any `bk` command, verify authentication:

```bash
bk auth status
```

If the output shows a 401 or no token, ask the user to run:

```bash
bk auth login
```

Do not attempt to proceed with `bk` commands if auth is missing — they will all return 401.

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

**`--org` flag does not exist**: `bk build view` has no `--org` flag — use `--pipeline <org>/<pipeline>` or `-p <org>/<pipeline>`. The org is embedded in the pipeline slug.

```bash
bk build view                                              # most recent (auto-detects from git)
bk build view <build-number> --pipeline <org>/<pipeline>
bk build list --pipeline <org>/<pipeline>
bk build list --pipeline <org>/<pipeline> --branch <branch> --state failed --since 24h
```

**GitHub merge queue branches** follow the pattern `gh-readonly-queue/main/pr-<number>-<sha>`. Passing the exact branch to `--branch` only works if you know the full name. To find merge queue builds by PR number, list all builds and grep:

```bash
bk build list --pipeline org/pipeline --no-limit -o json | grep -v '^[A-Z]' | \
  jq -r '.[] | "\(.number) \(.state) \(.created_at) \(.branch)"' | grep "pr-1598"
```

**`bk build list --no-limit -o json` can fail with a JSON marshal error** — `json: cannot unmarshal string into Go struct field Job.jobs.signal of type int`. This happens when certain job types (e.g. trigger steps) have unexpected field types. Fall back to `bk build view <number>` per-build instead of listing all builds at once.

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

## Dynamic per-step Slack notifications

`buildkite-agent step update "notify" '<json>' --append` (run from inside a step's own `command`) sets/appends that **same step's** per-step `notify` attribute at runtime — it does NOT target a step keyed/labeled `"notify"` elsewhere in the pipeline. `"notify"` here is the attribute name, not a step selector; with no `--step <id/key>` flag it defaults to the currently-running job's own step (via `BUILDKITE_STEP_ID`). This lets any step conditionally post to Slack (e.g. only when a check found something worth flagging) without a static top-level `notify:` block, and without a webhook or secret — it rides the org's existing Buildkite Slack integration.

```bash
# Inside a step's command, after producing a payload conditionally:
payload='[{"slack": {"channels": ["#my-channel"], "message": "..."}}]'
buildkite-agent step update "notify" "$payload" --append
```

Any step can run this regardless of its own `key`/`label` — no placeholder step named `"notify"` is required.

## Job and Log Operations

There is no `--build` flag for `bk job list` — use `bk build view` and parse the JSON instead.

```bash
bk job log <job-id>
bk job log <job-id> --no-timestamps
```

**`bk job log` prefixes every line with `_bk;t=<unix-ms>`** — use `--no-timestamps` to strip these prefixes. Without this flag, `grep` on specific patterns requires extra effort; with it, output is plain text ready for `grep`/`sed`/`head`.

**Job UUIDs are globally unique** — `--pipeline` and `--build-number` are deprecated and ignored by `bk job log`. Just pass the job ID.

**`bk job log` does NOT support `-o json`.**

**Large logs**: use `head -N` instead of `tail -N` or `grep` — `head` exits early via SIGPIPE and is significantly faster. For pipeline YAML, download the artifact instead:
```bash
# List artifacts — build number is positional, pipeline is -p
bk artifacts list <build-number> -p <org>/<pipeline>

# Download a specific artifact — no --destination flag; file lands in CWD
bk artifacts download <artifact-id> --build <build-number> -p <org>/<pipeline> -y
# Then read: cat <filename>  (filename comes from the artifact path field in list output)
```

**`bk artifacts download` gotchas**:
- No `--destination` flag — file always downloads to the current working directory
- `--build` and `-p` are required when specifying an artifact ID
- Use `-y` to skip the confirmation prompt in non-interactive shells

**`bk build view -o json` warning prefix**: output starts with a deprecation warning before the JSON. Strip it with `grep` before piping to `jq`:
```bash
bk build view 63 -p org/pipeline -o json | grep -v '^[A-Z]' | jq -r '.state'
```
Prefer `jq` for simple Buildkite JSON extraction; use another parser when it makes a complex transformation clearer.

**Empty log output**: either a trigger step (check the downstream build) or expired logs. Fall back to reading the build script from the local repo or via `gh api`.

**Trigger-step jobs have no logs of their own** — a job with `"type": "trigger"` just kicks off another pipeline's build; `bk job log` on it is always empty. To inspect what actually happened, pull the full job object and follow `.triggered_build`:

```bash
jq -r '.jobs[] | select(type=="object") | select(.name=="Trigger Version Bump for foo") | .triggered_build' build.json
# => {"number": 17, "url": "https://api.buildkite.com/v2/organizations/.../pipelines/foo-version-bump/builds/17", "web_url": "..."}

bk build view 17 --pipeline org/foo-version-bump -o json | grep -v '^[A-Z]' | jq -r '{state, branch, commit, env}'
```

This also lets you diff exactly what two runs of a fan-out/orchestrator pipeline actually sent downstream (env vars, branch, commit) per triggered repo — don't assume two runs behaved identically just because the top-level build's own env matched.

**Pipeline slug ≠ repo name** — `bk pipeline view <org>/<pipeline> -o json | jq '{repository, default_branch}'` shows the actual git repo and default branch backing a pipeline. A centralized/orchestrator pipeline's slug can differ from its source repo (e.g. pipeline `centralized-version-bump` is defined in repo `release-automation`) — check this before assuming which repo's branches affect its behavior.

**`.jobs[]` array contains literal `null` entries** (group/wait step separators) and some job objects have `name: null`. Any filter using `test()`, string interpolation, or other string ops on `.name`/`.state` fails with `jq: error ... null (null) cannot be matched, as it is not a string` unless guarded:
```bash
# ❌ breaks on null array entries or null .name fields
jq -r '.jobs[] | select(.name | test("Fetch"))'

# ✅ guard with select(type=="object") first
jq -r '.jobs[] | select(type=="object") | select(.name and (.name | test("Fetch")))'
```

## Common Workflows

```bash
bk build rebuild <build-number> --pipeline <org>/<pipeline>
bk build cancel <build-number> --pipeline <org>/<pipeline>
bk build view <build-number> --pipeline <org>/<pipeline> --web
```

### Retrying a failed step (transient failures)

**Prefer retrying the specific failed job over rebuilding the entire build.** Full rebuilds re-run steps that already passed, wasting time and resources. For transient failures (GCS 503s, network blips, flaky infra), identify the failed job and retry just that step:

```bash
# 1. Find the failed job ID
bk build view <build-number> -p <org>/<pipeline> -o json | grep -v '^[A-Z]' | \
  jq -r '.jobs[] | select(type=="object") | select(.state == "failed") | "\(.id) \(.name)"'

# 2. Retry the job — native command, confirmed working
bk job retry <job-id> -y
```

**Do not use `curl` + `bk api-token`/`$(bk auth token)` to hit the retry API directly** — that extracts a token from one command's output and passes it to another, which violates the "never extract secrets/tokens and pass them to another tool" rule. `bk job retry` covers this natively; there's no need for the manual workaround. Fall back to the web UI (build page → failed step → Retry) only if `bk job retry` itself fails.

**When to use full rebuild vs step retry**:
- Transient infra failure (503, timeout, network blip) → retry the step
- Code change needed → rebuild from scratch after the fix is merged
- Downstream triggered build failed → rebuild the downstream pipeline directly (not the parent)

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
bk job log $FIRST_JOB | head -100

# 4. Search logs for error patterns (e.g., "Error", "FAIL", "panic")
echo "--- Error summary ---"
bk job log $FIRST_JOB | grep -iE "(error|fail|panic|exception)" | head -20
```

**Tips**:
- **Multiple failed jobs**: Loop through `jq -r '.jobs[] | select(.state == "failed") | .id'` to check all failures
- **Large logs**: Use `head -N` to peek at the start, or `grep <pattern>` to find specific errors — avoid `tail -N` which buffers the entire log
- **Specific line range**: `bk job log <id> | sed -n '50,150p'` to view lines 50–150
- **Web view**: `bk build view <build-number> --pipeline <org>/<pipeline> --web` to open in browser and inspect interactively

## Build Meta-data Scope

`buildkite-agent meta-data set/get` is **scoped to a single build** — a later build cannot read meta-data set by an earlier build. Do not propose it for cross-build state persistence (e.g. "record last-built commit, read on next run"). For cross-build state, use the Buildkite REST API to query past builds (`GET /organizations/{org}/pipelines/{slug}/builds?state=passed&per_page=1`) and read the `.commit` field — or use an external store.

## Sandbox / Permissions

If `bk` cannot reach the API, ask the user to authenticate or approve the scoped command. Do not fall back to scraping the web UI.
