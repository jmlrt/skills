---
name: golang-development
description: "Guide Go development and code review. Apply when writing, maintaining, or reviewing Go code to ensure consistency with project tooling, module conventions, and common patterns."
allowed-tools: "Read, Grep, Glob, Edit, Write, Bash"
argument-hint: ""
user-invocable: false
---

# Go Development

Apply this skill when writing, maintaining, or reviewing Go code.

---

## Supporting Files

- **[tooling.md](tooling.md)** — Makefile targets, golangci-lint v2 config, CI toolchain conventions, GOTOOLCHAIN behavior
- **[patterns.md](patterns.md)** — Error handling, struct layout, and common patterns

---

## Mode Detection

| Signal | Mode |
|---|---|
| "write", "create", "add", "scaffold", "implement", "new" | **WRITE** |
| "fix", "refactor", "update", "change", "migrate", "improve" | **MAINTAIN** |
| "review", "check", "audit", "look at", "what do you think" | **REVIEW** |

---

## WRITE Mode

### Step 1: Greenfield or brownfield?

**Greenfield** (new repo or new package):
- Use templates from [tooling.md](tooling.md) as starting point
- Standard layout: `cmd/` for entry points, `internal/` for private packages, `pkg/` for public packages
- Apply all rules below from the start

**Brownfield** (existing repository):
- Read existing `Makefile`, `golangci-lint` config, and `go.mod` before writing anything
- Match existing patterns — don't retrofit conventions the repo hasn't adopted
- Check `CLAUDE.md` / `AGENTS.md` for repo-specific guidance first

### Step 2: Apply when writing any code

**Linter compliance** — read the repository's golangci-lint configuration before changing code. Common rules that surprise people:
- `noinlineerr`: split `if err := x(); err != nil` into two lines — see [patterns.md](patterns.md#error-handling)
- `wsl_v5`: add a blank line before `if` when multiple statements precede it
- `revive`: mark unused parameters with `_`

**Error handling:**
- Never swallow errors — always check and propagate or wrap
- Wrap with context: `fmt.Errorf("doing X: %w", err)`
- See [patterns.md](patterns.md#error-handling) for the noinlineerr split pattern

**Module hygiene:**
- `go.mod` `go` directive = minimum Go version required to build — see [tooling.md](tooling.md#gotoolchain) before bumping it

---

## MAINTAIN Mode

1. **Read before writing** — check existing patterns with Read/Grep
2. **Run checks after editing** — `make lint` and `make test`; see [tooling.md](tooling.md) for standard targets
3. **Match existing patterns** — preserve style even if it differs from greenfield defaults
4. **Don't change tooling** unless the user explicitly asks

---

## REVIEW Mode

Go through the diff and report findings. See [patterns.md](patterns.md) for detailed pattern checks.

### Blockers (Critical — must fix before merge)
- [ ] Swallowed errors: `err` returned but not checked, or `_ = someFunc()` on error-returning function
- [ ] `|| return 0` / `|| true` in shell scripts in the repo — silently converts failures to success; see review-pull-request skill
- [ ] `go.mod` `go` directive bumped above the CI toolchain version when `GOTOOLCHAIN=local` — will fail all pipelines; see [tooling.md](tooling.md#gotoolchain)
- [ ] Secrets or credentials hardcoded
- [ ] Race conditions: shared state accessed without synchronization

### Suggestions
- [ ] Missing error wrapping context (`fmt.Errorf("...: %w", err)` preferred over bare `err`)
- [ ] Inline error assignment not split for `noinlineerr` lint rule (will fail CI)
- [ ] Missing blank line before `if` block when multiple statements precede it (`wsl_v5`)
- [ ] Unused parameter not named `_` (`revive`)

### NITs
- [ ] Abbreviated variable name where the full word is short and unambiguous (`bid` → `buildID`, `pkgs` → `packages`, `p` for a package struct → `pkg`) — see [patterns.md](patterns.md#naming)
- [ ] Exported identifier missing godoc comment
- [ ] Magic constant that should be a named `const`
- [ ] Test helper not calling `t.Helper()`
- [ ] Error string contains `\n` — Go style requires single-line errors; see [patterns.md](patterns.md#error-strings)
- [ ] Package named `validate`, `util`, `helper`, `common` — too generic; prefer a name that describes what the package actually does (e.g. `layout`, `checksum`, `dralayout`)

**For version bump PRs**: always check GOTOOLCHAIN behavior — see [tooling.md](tooling.md#gotoolchain).

When a blocker is found, grep for the same pattern across the codebase and include all instances in the review comment.

---

## Brownfield Decision Tree

**golangci-lint config present?**
- Yes → run `make lint` with existing config; don't add or remove linters
- No → add `.golangci.yml` only if the user asks

**Go version in `go.mod`?**
- Check against CI toolchain before bumping — see [tooling.md](tooling.md#gotoolchain)

**Makefile present?**
- Yes → check for `test`, `lint`, `fmt`, `build` targets; use them
- No → run `go test ./...` and `golangci-lint run` directly
