# Go Patterns

## Switch case shadowing

`:=` in a `switch` case declares new variables scoped to the case. Re-declaring a parameter that is returned loses the
mutation:

```go
// Bug: rows is a new local in the case
case cond:
    rows, idx := transform(rows)
    rows[idx].Field = value
// ...
return rows // original rows

// Fix
var idx int
case cond:
    rows, idx = transform(rows)
```

Flag any case that uses `:=` to reassign a parameter or named return used in `return`.

## Naming

- Avoid abbreviations a reader has to guess: `bid` → `buildID`, `pkgs` → `packages`, `p` → `pkg`, `cfg` → `config`.
- Fine: single-letter params mirroring the type (`r io.Reader`), short loop vars, `err`.
- When the natural name collides with the package (`manifest`), use a compound (`builtManifest`), not a single letter.

## Not a bug

`filepath.Walk` callbacks with `if err != nil || info.IsDir() { return err }` are idiomatic: don't flag.
