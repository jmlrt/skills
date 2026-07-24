# Go Patterns

Common patterns for writing and reviewing Go code.

## Quick Navigation

- [Error Handling](#error-handling) — noinlineerr split, wrapping, propagation
- [Error Strings](#error-strings) — single-line rule, no embedded newlines
- [Struct Layout](#struct-layout) — field ordering, constructor conventions
- [Standard Idioms](#standard-idioms) — filepath.Walk, and other patterns not to flag
- [goconst](#goconst) — define AND use constants; cross-file counting
- [wsl_v5](#wsl_v5) — blank line before `if` only when 2+ statements precede it
- [Shell Scripts in Repos](#shell-scripts-in-repos) — error handling anti-patterns

---

## Error Handling

### The noinlineerr split (required by golangci-lint)

golangci-lint's `noinlineerr` rule requires splitting inline error assignments out of `if` conditions.

```go
// ❌ Will fail CI
if err := db.Connect(ctx); err != nil {
    return fmt.Errorf("connecting to db: %w", err)
}

// ✅ Correct
err := db.Connect(ctx)
if err != nil {
    return fmt.Errorf("connecting to db: %w", err)
}
```

### Error wrapping

Always add context when wrapping errors. Use `%w` (not `%v`) so callers can use `errors.Is` / `errors.As`:

```go
// ✅ Wraps with context, preserves error chain
return fmt.Errorf("loading config from %s: %w", path, err)

// ❌ Loses error chain (callers can't errors.Is check)
return fmt.Errorf("loading config from %s: %v", path, err)
```

### Never swallow errors

```go
// ❌ Swallowed — silent failure
result, _ := doSomething()

// ✅ Check and propagate or explicitly decide to ignore with a comment
result, err := doSomething()
if err != nil {
    return fmt.Errorf("doing something: %w", err)
}
```

### Sentinel errors and `errors.Is`

```go
var ErrNotFound = errors.New("not found")

// Wrap sentinel so callers can check it
return fmt.Errorf("fetching release %s: %w", tag, ErrNotFound)

// Caller
if errors.Is(err, ErrNotFound) {
    // handle missing resource
}
```

---

## Error Strings

Go style requires error strings to be single-line. Embedding `\n` makes errors hard to grep in logs and breaks `%w` wrapping readability. See [Go decisions — error strings](https://google.github.io/styleguide/go/decisions#error-strings).

```go
// ❌ Multi-line — hard to grep, breaks wrapping
return fmt.Errorf(
    "required prefix not found: dra/%s/%s/\n  expected at: %s",
    productID, versionBuildID, prefix,
)

// ✅ Single-line
return fmt.Errorf("required prefix dra/%s/%s/ not found, expected at: %s", productID, versionBuildID, prefix)
```

---

## Struct Layout

Conventional struct field ordering:

```go
type ReleaseConfig struct {
    // Identity fields first
    Name    string
    Version string

    // Configuration
    Branch  string
    DryRun  bool

    // Internal/computed fields last, unexported
    client *http.Client
    logger *slog.Logger
}
```

**Constructors**: use `New*` prefix, return `(*T, error)` when initialization can fail:

```go
func NewReleaseConfig(name, version string, opts ...Option) (*ReleaseConfig, error) {
    cfg := &ReleaseConfig{
        Name:    name,
        Version: version,
        client:  http.DefaultClient,
    }
    for _, opt := range opts {
        if err := opt(cfg); err != nil {
            return nil, fmt.Errorf("applying option: %w", err)
        }
    }
    return cfg, nil
}
```

---

## Naming

Avoid abbreviated variable names when the full word is short and the abbreviation obscures meaning:

```go
// ❌ Abbreviations that lose meaning
bid := buildid.Generate(version)   // bid — a financial bid? a command?
pkgs := make(map[string]*Package)  // pkgs — close, but packages is clearer
p, err := classify.FromFilename()  // p — which of 10 things starting with p?

// ✅ Full names
buildID := buildid.Generate(version)
packages := make(map[string]*Package)
pkg, err := classify.FromFilename()
```

**Acceptable short names:**
- Single-letter function parameters that mirror the type (`m *Manifest`, `r io.Reader`, `w io.Writer`) — idiomatic Go for receiver-style params where the type is visible at the declaration
- Loop variables (`i`, `k`, `v`) in short, obvious loops
- Error variable `err` — universal Go convention

**Package-name collision**: when the natural name for a local variable is already the package name (e.g. naming a `*manifest.Manifest` value `manifest`), use a descriptive compound name instead of falling back to a single letter:

```go
// ❌ Single letter to avoid shadowing — still unclear
m, err := manifest.Build(opts)

// ✅ Compound name that doesn't shadow the package
builtManifest, err := manifest.Build(opts)
```

**Red flags:** any abbreviation where a reader outside the immediate context would have to guess what it stands for (`bid`, `bld`, `mf`, `conf`, `cfg` when `config` fits, `prod` when `productID` fits).

---

## Standard Idioms

Patterns that look unusual but are idiomatic Go — do not flag these in review.

### `filepath.Walk` callback

```go
filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
    if err != nil || info.IsDir() {
        return err
    }
    // process file
})
```

The combined condition `if err != nil || info.IsDir() { return err }` is standard. When `info.IsDir()` is true, `err` is nil, so `return err` returns nil — telling Walk to descend into the directory. When `err != nil`, it propagates the error and aborts. Two separate conditions would be clearer but this form is idiomatic and widely used.

---

## Shell Scripts in Repos

Go repositories often include shell scripts (`.sh`, `.bash`) alongside Go code. Common anti-patterns to flag in review:

### `|| return 0` / `|| true` (Critical)

Silently converts any failure into success. Only safe when the specific error case is exhaustively handled; all other failures should propagate:

```bash
# ❌ Critical — swallows network errors, auth failures, etc.
result=$(gh api repos/owner/repo/pulls/123) || return 0

# ✅ Acceptable only if 404 is the ONLY expected failure and you handle it explicitly
http_code=$(gh api repos/owner/repo/pulls/123 -i 2>/dev/null | head -1 | awk '{print $2}')
if [[ "$http_code" == "404" ]]; then
    return 0  # not found — expected
fi
# all other errors: propagate naturally via set -e or explicit check
```

### Missing `set -euo pipefail`

Scripts without strict mode silently continue after failures:

```bash
# ✅ Recommended shell-script header
#!/usr/bin/env bash
set -euo pipefail
```

### Error messages to stdout instead of stderr

```bash
# ❌ Goes to stdout — pollutes captured output
echo "Error: something failed"

# ✅ Goes to stderr
echo "Error: something failed" >&2
```

---

## goconst

`goconst` fires in two distinct cases — both require action:

1. **No constant exists**: string appears 3+ times → define a constant and use it everywhere.
2. **Constant exists but string literal is still used**: error message says "but such constant `X` already exists" → replace all literal occurrences with the constant.

Simply defining the constant is not enough; you must also replace every literal usage.

**Cross-file counting**: `goconst` counts across all `.go` files in the same directory, including both `package foo` and `package foo_test` files. A string repeated in `foo.go` and `foo_test.go` counts toward the threshold combined. Implications:
- If both files are in the same package (`package foo`), an unexported constant in `foo.go` satisfies the linter for both files.
- If the test file is an external test package (`package foo_test`), the constant must be **exported** for the test file to use it — or the test file must define its own local constant.

**`replace_all` pitfall with constant definitions**: when using the Edit tool's `replace_all` to swap a string literal for a constant name, it will also replace the string on the constant's own definition line — producing an initialization cycle:

```go
// Before: testFoo = "bar" appears 3 times → goconst fires
// You add: const testFoo = "bar"
// Then replace_all "bar" → testFoo ...
const testFoo = testFoo  // ❌ initialization cycle
```

Use a targeted edit for the constant definition line, then `replace_all` only for the usage lines. Or define the constant first, save, then replace usages.

---

## Switch/case `:=` shadowing (slice mutation lost)

`:=` inside a `switch` case block declares new variables scoped to that case. If a function parameter (e.g. a slice) is re-declared with `:=`, mutations to it are invisible to the caller and never reach the `return`.

```go
// ❌ Bug: rows inside each case is a new local variable
func addEntry(rows []Row, ...) []Row {
    switch {
    case ...:
        rows, idx := transform(rows, ...)  // shadows outer rows
        rows[idx].Field = value            // mutates local copy only
    }
    return rows  // returns original, unmodified rows
}

// ✅ Fix: declare idx separately, use = for rows
func addEntry(rows []Row, ...) []Row {
    var idx int
    switch {
    case ...:
        rows, idx = transform(rows, ...)   // assigns to outer rows
        rows[idx].Field = value
    }
    return rows
}
```

Flag in review any `switch` case that uses `:=` to reassign a function parameter or named return that is also used in `return`.

---

## wsl_v5

`wsl_v5` requires a blank line before an `if` statement **only when 2 or more statements precede it** in the same block (without an intervening blank line). One preceding statement → no blank line needed.

```go
// ✅ 1 preceding statement — no blank line needed
err := doSomething()
if err != nil {
    return err
}

// ✅ 2 preceding statements — blank line required before if
x := computeX()
y := computeY()

if x > y {
    return x
}
```

wsl_v5 also requires a blank line after every closing `}` before the next statement.
