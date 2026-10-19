---
name: golang-development
description: "Guide Go development and code review. Apply when writing, maintaining, or reviewing Go code to ensure consistency with project tooling, module conventions, and common patterns."
allowed-tools: "Read, Grep, Glob, Edit, Write, Bash"
argument-hint: ""
user-invocable: false
---

# Go Development

Personal tooling defaults and non-obvious patterns. Generic Go knowledge is assumed.

## Supporting Files

- **[tooling.md](tooling.md)** — read when a golangci-lint v2 rule fails, or before bumping the `go` directive
- **[patterns.md](patterns.md)** — read when reviewing Go code for subtle bugs and naming

## Defaults

- **Greenfield**: `cmd/` entry points, `internal/` private packages; golangci-lint v2 with `default: all`; `make`
  targets `test`, `lint`, `fmt`, `build`.
- **Brownfield**: read `Makefile`, `.golangci.yml`, `go.mod`, and `CLAUDE.md` / `AGENTS.md` first. Match existing
  patterns, don't add or remove linters, don't change tooling unless asked. No Makefile → `go test ./...` and
  `golangci-lint run`.
- After editing: `make lint` and `make test`.
- Wrap errors with context (`fmt.Errorf("doing X: %w", err)`); never swallow them.
- `go.mod` changes ship with `go.sum`; if `vendor/` exists, run `go mod vendor` too.

## Review Checklist

### Blockers

- Swallowed errors (`_ = f()` on an error-returning function, unchecked `err`)
- `go` directive bumped above the CI toolchain with `GOTOOLCHAIN=local` — see [tooling.md](tooling.md#gotoolchain)
- `:=` inside a `switch` case shadowing a returned parameter — see [patterns.md](patterns.md#switch-case-shadowing)
- `|| true` / `|| return 0` in repo shell scripts
- Hardcoded secrets; shared state without synchronization

### Suggestions

- Lint rules that fail CI: `noinlineerr`, `wsl_v5`, `revive`, `godot`, `goconst` — see [tooling.md](tooling.md)
- Missing error wrap context

### NITs

- Abbreviated names (`bid`, `pkgs`, `p`) — see [patterns.md](patterns.md#naming)
- Generic package names (`util`, `helper`, `common`, `validate`)
- Multi-line error strings (`\n` in `fmt.Errorf`)
- Test helper without `t.Helper()`; magic constants

When a blocker is found, grep for the same pattern across the codebase and list every instance.
