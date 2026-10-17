---
name: englog
description: Read and update the day's time log with the englog CLI. Use when the user asks what they worked on today, to start or stop a time entry, to log a forgotten entry at a past time, or to inspect a daily time file.
---

# Englog

Use [Englog](http://github.com/jmlrt/englog) to log the workday as time entries in `$ENGLOG_DIR/YYYY-MM-DD.txt`.
Default to read-only access; write only when the user asks.

## Read

```bash
englog status   # running entry and today's total
englog list     # today's entries with durations
```

For another day, read `$ENGLOG_DIR/YYYY-MM-DD.txt` directly.

## Write

```bash
englog start day prep, check notifs     # ends the running entry; no quotes needed
englog start --at 14:20 1/1 alice       # forgot to log: start at a past time
englog stop                             # or: englog stop --at 17:45
```

- Options go before the title: everything after `--at HH:MM` is the title.
- Characters the shell treats specially (`( ) ; & | < > * ? ' "`) still need quoting.
- `--at` can't be in the future or earlier than the last line. For any other fix, edit the file directly and keep the
  lines in time order.
- Verify a write with `englog list`.

## File format

One `HH:MM title` line per entry. `HH:MM stop` ends the running entry (a break, or the end of the day). An entry ends
when the next line starts and durations are computed, so never write a duration.

```
09:00 day prep, check notifs
09:30 1/1 alice
10:00 stop
```

If the CLI is unavailable, edit the daily file directly rather than guessing an installation path.
