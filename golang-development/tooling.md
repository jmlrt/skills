# Go Tooling

## golangci-lint v2 rules that surprise people

Check the repo's `.golangci.yml` first: these apply when the linter is enabled.

- **`noinlineerr`**: split `if err := f(); err != nil` into `err := f()` then `if err != nil`.
- **`wsl_v5`**: blank line before `if` only when 2+ statements precede it in the block; blank line after every
  closing `}` before the next statement.
- **`revive`**: unused parameters must be named `_`.
- **`godot`**: every comment ends with a period, including internal and format-string comments.
- **`modernize`**: prefer `strings.Cut` over `strings.Index` + slicing.
- **`gocyclo`** (limit 30): extract a helper, don't add an exclusion. `cyclop` is often disabled while `gocyclo` is
  not: check which one is active.
- **`maintidx`**: large table-driven tests fail it; exclude it for `_test\.go` paths rather than splitting tables.

### goconst

- Fires both when no constant exists (3+ repeats) and when a constant exists but literals remain: replace every
  literal usage, not just define the constant.
- Counts across all files in the directory, including `_test.go`. An external `package foo_test` needs an exported
  constant or its own local one.
- `replace_all` of the literal also rewrites the constant's definition (`const x = x`, initialization cycle): edit the
  definition line separately.

## GOTOOLCHAIN

With `GOTOOLCHAIN=local` (common in CI), Go refuses to build when the `go` directive exceeds the installed toolchain:
`go: toolchain go1.X.Y not found and GOTOOLCHAIN=local`. No auto-download.

Before approving a `go` directive bump (Renovate/Dependabot included), compare it with the CI Go version:

```bash
grep -r "go-version\|golang\|image.*go" .buildkite/ .github/workflows/ Dockerfile* 2>/dev/null
head -5 go.mod
```

Bump above the CI version with `GOTOOLCHAIN=local` → **Critical**, every pipeline fails.
