---
name: untracked-secrets-scan
description: "Find untracked files that may contain secrets across local git repos (e.g. ~/Code), report paths only, and help clean up. Use when the user asks to audit repos for env files, keys, credentials or Terraform leftovers that are not committed."
allowed-tools: "Bash(find:*), Bash(git:*), Bash(bash:*), Bash(grep:*), Bash(sort:*), Bash(awk:*), Bash(wc:*)"
argument-hint: [root directory, default ~/Code]
---

# Untracked secrets scan

Lists files that look like secrets and are **not tracked by git**. Tracked files are assumed safe, so only untracked
ones (including gitignored ones) are reported.

## Hard rules

- **Never read flagged files**: no `cat`, `Read`, `head`, `grep` on their contents. Report paths only, the user checks
  them.
- **Never touch `.envrc`**: report the path, the user cleans it.
- **Delete only after the user reviewed the files**, and confirm per group. Only untracked files are in scope.

## Scan

Write the script to the session scratchpad and run it in the background (takes more than 2 minutes on `~/Code`):

```bash
#!/bin/bash
ROOT=${1:-~/Code}
check() { # label, find-args...
  label=$1; shift
  find "$ROOT" \( -name node_modules -o -name .git -o -name .venv -o -name vendor -o -name target -o -name dist \) -prune -o \
    -type f \( "$@" \) -size -1024k -print 2>/dev/null | sort | while read -r f; do
    d=$(dirname "$f"); b=$(basename "$f")
    if ! git -C "$d" rev-parse --is-inside-work-tree >/dev/null 2>&1; then echo "$label NOGIT $f"
    elif git -C "$d" ls-files --error-unmatch "$b" >/dev/null 2>&1; then :
    else echo "$label UNTRACKED $f"; fi
  done
}
check ENV -name '.env' -o -name '.envrc' -o -name '.secrets*' -o -name '.env.*' -o -name '*.env' -o -name 'secrets.*'
check KEYS -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name '*.pfx' -o -name '*.jks' -o -name '*.keystore' -o -name 'id_rsa*' -o -name 'id_ed25519*' -o -name 'id_ecdsa*' -o -name '*.gpg' -o -name '*.asc'
check CREDS -name 'credentials.json' -o -name 'service-account*.json' -o -name '*-sa.json' -o -name '.netrc' -o -name '.npmrc' -o -name '.pypirc' -o -name '.dockercfg' -o -name '.git-credentials' -o -name 'kubeconfig*' -o -name '*.kubeconfig' -o -name '.vault-token' -o -name '.terraformrc' -o -name 'terraform.tfvars' -o -name '*.auto.tfvars' -o -name 'terraform.tfstate*'
check LOCAL -name 'settings.local.json' -o -name 'CLAUDE.local.md' -o -name '*.local.yaml' -o -name '*.local.yml' -o -name '*.local.json'
check NAME -name '*secret*' -o -name '*credential*' -o -name '*token*' -o -name '*password*'
```

Run as `bash scan.sh > "$SCRATCH/scan.out"` with `run_in_background`, then read the output file once notified. Use
`bash`, not zsh (zsh reserves `path` and `status`).

## Filter the output

Raw output is ~1,400 lines, mostly noise. Cut it down:

```bash
grep -v -e '/venv/' -e '/site-packages/' -e '\.pyc$' -e '/\.terraform/' -e '/\.terragrunt-cache/' \
  -e 'settings.local.json' "$SCRATCH/scan.out"
```

Typical noise: `cacert.pem` in venvs, `secrets.cpython-*.pyc`, `kubeconfig*.pyc`, docs named `*token*` or `*secret*`,
`NOGIT` worktree docs. Judgment calls without reading:

- `*.asc` / `Release.gpg` are usually detached signatures, public data.
- `CLAUDE.local.md` is instructions, not credentials.
- Source files matching only on name (`secrets.py`) are code.

Report remaining paths grouped (env files, keys, Terraform, other) and say which ones are probably fine.

## Review and cleanup

- For the user to inspect files, give a **self-contained** command to run in their own shell (re-declare every variable,
  e.g. a `for f in ...; do echo "== $f"; cat "$f"; done` over the explicit list).
- Terraform leftovers: `.terraform/terraform.tfstate` is only backend config (`terraform init` regenerates it);
  `*.auto.tfvars` and `credentials.json` need the user's check first.
- If the user says to delete, `rm -v` the explicit paths (never a glob), then report what was removed and what was
  already missing.
- After cleanup, rerun the scan and report only what remains.

## Blind spots to mention

- Pruned dirs (`node_modules`, `vendor`, `target`, `dist`, `.venv`) and files over 1 MB.
- Backport CLI clones (`~/.backport/`) can embed a PAT in the remote URL. Don't print git config; the user can run
  `grep -l 'https://[^/@ ]*@' ~/.backport/repositories/*/*/.git/config` (file names only).
- Locations outside the root (`~/.aws`, `~/.okta`, `~/.netrc`, `~/.config`).
- Secrets inside files with ordinary names: names only are matched. Use `gitleaks` or `trufflehog` (including git
  history).
