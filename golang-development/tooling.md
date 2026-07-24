# Go Tooling

Reference for build tooling, linting configuration, and CI conventions in Go repositories.

## Quick Navigation

- [Standard Makefile Targets](#standard-makefile-targets) — test, lint, fmt, build
- [golangci-lint v2](#golangci-lint-v2) — config, key rules, common failures
- [GOTOOLCHAIN](#gotoolchain) — local vs auto, version bump safety check
- [Module Conventions](#module-conventions) — go.mod, go.sum, vendoring

---

## Standard Makefile Targets

Many Go repositories expose these targets:

```
make test    # run tests (go test ./...)
make lint    # run golangci-lint
make fmt     # run gofmt / goimports
make build   # compile binary
```

Always check `make help` or read the `Makefile` — some repos add `check` (lint + test), `generate`, or `release` targets.

---

## golangci-lint v2

Some Go repositories use golangci-lint v2 with `default: all` (all linters enabled, then selectively disabled). Check the repository's configuration before assuming this setup.

### Running

```bash
golangci-lint run           # lint all packages
golangci-lint run ./...     # explicit
golangci-lint run --fix     # auto-fix where supported
```

### Key rules that surprise people

**`noinlineerr`** — inline error assignments in `if` conditions must be split:

```go
// ❌ Will fail noinlineerr
if err := doSomething(); err != nil {
    return err
}

// ✅ Correct
err := doSomething()
if err != nil {
    return err
}
```

**`wsl_v5`** — blank line required before `if` (and other blocks) when preceded by multiple statements:

```go
// ❌ Will fail wsl_v5
x := foo()
y := bar()
if x > y {

// ✅ Correct
x := foo()
y := bar()

if x > y {
```

**`modernize`** — prefer `strings.Cut` over `strings.Index` + manual slicing when splitting on a separator into two parts:

```go
// ❌ Will fail modernize
colonIdx := strings.Index(s, ":")
if colonIdx < 0 {
    return errors.New("missing :")
}
left, right := s[:colonIdx], s[colonIdx+1:]

// ✅ Correct
left, right, ok := strings.Cut(s, ":")
if !ok {
    return errors.New("missing :")
}
```

**`maintidx`** — large table-driven test functions score below the default maintainability threshold. Rather than splitting the table, exclude `maintidx` for test files in `.golangci.yml`:

```yaml
exclusions:
  rules:
    - linters:
        - maintidx
      path: _test\.go
```

**`godot`** — all comments (not just exported godoc) must end in a period. This includes internal function comments and inline format-string comments like `// Filename: {name}-{version}.ext`:

```go
// ❌ Will fail godot
// Filename: {name}-{version}[-{classifier}].{ext}
func parse(s string) {}

// ✅ Correct
// Filename: {name}-{version}[-{classifier}].{ext}.
func parse(s string) {}
```

**`gocyclo`** — cyclomatic complexity limit is 30. Large functions with many branches (switch arms, nested ifs, error checks) can hit it during refactors that look like simplifications. Extract the complex block into a helper function; do not add a linter exclusion:

```go
// ❌ Inlining all cases into FromFilename pushes it over 30
func FromFilename(...) (Package, error) {
    // ... 30+ branches already ...
    switch product { case "beats": ... case "connectors": ... } // triggers gocyclo
}

// ✅ Extract the switch into a helper
func applyProductOverride(filename, stackVersion, product string, p Package) Package {
    switch product {
    case "beats": return beatsRule(filename, p)
    // ...
    }
    return p
}
```

Note: `cyclop` is often disabled in `.golangci.yml` but `gocyclo` usually is not — check which one is active before assuming the complexity check is off.

**`revive`** — unused parameters must be named `_`:

```go
// ❌ Will fail revive
func handler(w http.ResponseWriter, r *http.Request) {
    // r never used
}

// ✅ Correct
func handler(w http.ResponseWriter, _ *http.Request) {
```

---

## GOTOOLCHAIN

The `GOTOOLCHAIN` environment variable controls whether Go will auto-download a newer toolchain if `go.mod` requires one.

### `GOTOOLCHAIN=local` (common CI configuration)

Go will **only** use the installed toolchain version and will **refuse to run** if `go.mod`'s `go` directive requires a newer version. There is no fallback or auto-download.

**Impact on version bump PRs**: if a Renovate/Dependabot PR bumps the `go` directive in `go.mod` to a version newer than what CI agents have installed, **all CI jobs will fail** with:

```
go: toolchain go1.X.Y not found and GOTOOLCHAIN=local
```

### Safety check before approving a `go` directive bump

```bash
# Check what Go version CI agents use (look in CI pipeline config)
grep -r "go-version\|golang\|image.*go" .buildkite/ .github/workflows/ Dockerfile* 2>/dev/null

# Check what go.mod currently requires vs what's being bumped to
head -5 go.mod
```

If the bumped version exceeds the CI-installed version and `GOTOOLCHAIN=local` is set, flag as **Critical** — the PR will break CI and cannot auto-merge.

### `GOTOOLCHAIN=auto` (default in newer Go)

Go will auto-download the required toolchain if not installed. Safe for version bumps but requires outbound network access in CI.

---

## Module Conventions

**`go.mod` `go` directive** — sets the minimum Go version required to build. Bumping it is a breaking change for anyone building with an older toolchain.

**Vendoring** — some repositories use `vendor/`. Check for its presence before running `go get` or modifying `go.sum`:
```bash
ls vendor/ 2>/dev/null && echo "vendored" || echo "not vendored"
```
If vendored, run `go mod vendor` after any `go.mod` change.

**`go.sum`** — always commit alongside `go.mod` changes. If a PR modifies `go.mod` but not `go.sum`, it likely won't build.
