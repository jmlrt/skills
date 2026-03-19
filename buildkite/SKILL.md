---
name: buildkite
description: Interact with Buildkite using the bk CLI. Use when the user wants to trigger builds, check build status, list pipelines, view build logs, or perform any Buildkite operations from the command line.
allowed-tools: "Bash(bk:*), Bash(curl:*), Read"
argument-hint: [pipeline-slug or build-number]
---

# Buildkite CLI (`bk`)

## Prerequisites

Check if `bk` is installed:
```bash
which bk && bk --help | head -5
```

If not installed:
```bash
# macOS
brew install buildkite/buildkite/bk

# Or using Go
go install github.com/buildkite/cli/v3@latest
```

Authenticate (one-time setup):
```bash
bk configure
```

## Triggering Builds

### Basic build
```bash
bk build create --pipeline <org>/<pipeline> --branch <branch>
```

### With specific commit
```bash
bk build create --pipeline <org>/<pipeline> --branch <branch> --commit <sha>
```

### With environment variables
```bash
bk build create --pipeline <org>/<pipeline> \
  --branch <branch> \
  --commit <sha> \
  --env KEY1=value1 \
  --env KEY2=value2
```

### With a message
```bash
bk build create --pipeline <org>/<pipeline> --branch <branch> --message "My custom build"
```

### Example: Trigger with multiple env vars
```bash
bk build create \
  --pipeline org/pipeline-name \
  --branch feature-branch \
  --commit abc123def \
  --env BUILD_VERSION=1.2.3 \
  --env DRY_RUN=true \
  --env MANIFEST_URL=https://example.com/manifest.json
```

### Trigger and watch immediately
```bash
bk build create --pipeline <org>/<pipeline> --branch main --web
```

**`bk build create` prompts for confirmation**: The CLI prints `Create new build on <pipeline>? [Y/N]:` and waits. In non-interactive shells (Shell tool, CI) pipe a `Y` explicitly:
```bash
printf 'Y\n' | bk build create --pipeline <org>/<pipeline> --branch <branch> --message "..."
```

## Querying Build Status

### View a specific build
```bash
bk build view <build-number> --pipeline <org>/<pipeline>
```

### View most recent build (auto-detects from git repo)
```bash
bk build view
```

### List recent builds for a pipeline
```bash
bk build list --pipeline <org>/<pipeline>
```

### List builds filtered by branch
```bash
bk build list --pipeline <org>/<pipeline> --branch <branch>
```

### List builds filtered by state
```bash
bk build list --pipeline <org>/<pipeline> --state running
bk build list --pipeline <org>/<pipeline> --state passed
bk build list --pipeline <org>/<pipeline> --state failed
```

### List builds with time filters
```bash
bk build list --pipeline <org>/<pipeline> --since 1h
bk build list --pipeline <org>/<pipeline> --since 24h --state failed
```

### Build frequency analysis (multi-pipeline, multi-branch)

**Critical**: always pass `--no-limit` — the default cap is 50 results, which covers less than one day for high-frequency pipelines, silently truncating historical data.

**Branch scope**: always clarify whether counts are all-branch or filtered. Filter to the branches relevant to your context. All-branch counts are inflated by PR builds.

**Exclude today** (partial day distorts averages): filter `date < today` when aggregating.

**Low-activity pipelines**: if 0 builds in 3 days, automatically extend to 7 days then 10 days before concluding inactive.

**Parallel multi-pipeline pattern** (use Python ThreadPoolExecutor; `--no-limit` + date filter):

```python
import subprocess, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

TODAY = str(date.today())
pipelines = ["org/pipeline-a", "org/pipeline-b"]
branches = ["main", "1.x", "2.x"]

def query(slug, branch):
    r = subprocess.run(
        ["bk", "build", "list", "--pipeline", slug,
         "--branch", branch, "--since", "96h", "--no-limit", "-o", "json"],
        capture_output=True, text=True
    )
    builds = json.loads(r.stdout) if r.returncode == 0 else []
    counts = {}
    for b in builds:
        d = b.get("created_at", "")[:10]
        if d and d < TODAY:
            counts[d] = counts.get(d, 0) + 1
    return slug, branch, counts

tasks = [(p, b) for p in pipelines for b in branches]
with ThreadPoolExecutor(max_workers=20) as ex:
    futures = [ex.submit(query, *t) for t in tasks]
    for f in as_completed(futures):
        slug, branch, counts = f.result()
        days = sorted(counts)[-3:]
        avg = round(sum(counts[d] for d in days) / max(len(days), 1))
        print(f"{slug} [{branch}]: avg {avg}/day")
```

**Pipeline 404**: if a pipeline slug returns 404, mark it explicitly — slugs in docs can be stale/renamed. Don't silently skip or treat as 0 activity.

### Open build in web browser
```bash
bk build view <build-number> --pipeline <org>/<pipeline> --web
```

## Pipeline Operations

### List all pipelines
```bash
bk pipeline list
```

### View pipeline details
```bash
bk pipeline view <org>/<pipeline>
```

## Job and Log Operations

### List jobs in a build

There is no `--build` flag for `bk job list`. Instead, use `bk build view` and parse the JSON:
```bash
bk build view <build-number> --pipeline <org>/<pipeline>
# Extract job details with jq/python from the JSON output
```

**`bk build view -o json` warning prefix**: The output starts with a deprecation warning line (`Warning: reading API token from config file is deprecated...`) before the JSON. Direct `json.load(sys.stdin)` will fail. Strip non-JSON lines first:
```python
raw = subprocess.run(["bk", "build", "view", str(num), "--pipeline", slug, "-o", "json"],
                     capture_output=True, text=True).stdout
data = json.loads(next(l for l in raw.splitlines() if l.strip().startswith('{')))
# or: skip lines until first '{', then json.loads('\n'.join(lines[i:]))
```

### View job logs

**Important**: The `-b <build-number>` flag is required alongside the job ID. Without it, the command may return empty output silently.
```bash
bk job log <job-id> -p <org>/<pipeline> -b <build-number>
```

Add `--no-timestamps` for cleaner output when searching/grepping logs:
```bash
bk job log <job-id> -p <org>/<pipeline> -b <build-number> --no-timestamps
```

**Note**: `bk job log` does NOT support `-o json` or `-o yaml` (unlike other `bk` subcommands).

**Large log warning**: Some steps embed large outputs (full pipeline YAML, git clone progress) making the log 100 KiB+. `tail -N` and `grep` require downloading the entire log and can take 5–35 minutes. Use `head -N` instead — it exits early via SIGPIPE and is significantly faster for getting the first part of a log. For the pipeline YAML specifically, download the `pipeline.yaml` artifact instead:
```bash
bk artifacts list <build-number> --pipeline <org>/<pipeline>
bk artifacts download <artifact-id>
```

**Empty log output**: `bk job log` can return empty output for two reasons: (1) trigger steps execute no commands — check the downstream build instead; (2) script-type jobs on certain agent queues or with expired logs also return empty silently. If a script job's log is empty, fall back to reading the build script directly from the local repo or via `gh api`.

## Artifacts

### List artifacts for a build
```bash
bk artifacts list <build-number> --pipeline <org>/<pipeline>
```

### Download an artifact
```bash
bk artifacts download <artifact-id>
```

## Common Workflows

### Retry a failed build
```bash
bk build rebuild <build-number> --pipeline <org>/<pipeline>
```

### Cancel a running build
```bash
bk build cancel <build-number> --pipeline <org>/<pipeline>
```

## API Fallback (curl)

If `bk` CLI is unavailable, use the REST API directly:

```bash
export BUILDKITE_TOKEN="your-api-token"  # Needs write_builds scope

# Trigger a build
curl -X POST "https://api.buildkite.com/v2/organizations/<org>/pipelines/<pipeline>/builds" \
  -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "commit": "<sha>",
    "branch": "<branch>",
    "message": "Build triggered via API",
    "env": {
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }'

# Get build status
curl -s "https://api.buildkite.com/v2/organizations/<org>/pipelines/<pipeline>/builds/<number>" \
  -H "Authorization: Bearer $BUILDKITE_TOKEN" | jq '.state'
```

Get an API token at: https://buildkite.com/user/api-access-tokens

## Tips

- Use `-o json` or `-o yaml` for machine-readable output (supported by `build`, `pipeline` commands; NOT by `job log`)
- **Prefer `jq` over Python** for parsing `bk` JSON output: `bk build list -p org/pipeline -o json | jq -r '.[].state'`. Only use Python when the logic requires loops or aggregation that `jq` can't handle cleanly.
- Build numbers are integers; commits are full SHAs or `HEAD`
- Environment variables are strings; quote values with spaces
- Use `--web` or `-w` to open results in browser
- Short flags: `-p` (pipeline), `-b` (branch), `-m` (message), `-c` (commit), `-e` (env)

## Sandbox / Permissions

**Always use `required_permissions: ["all"]`** when running `bk` commands — the `["network"]` permission is NOT sufficient: the `bk` CLI fails with `tls: failed to verify certificate: x509: OSStatus -26276` inside the sandbox even with network access enabled.
