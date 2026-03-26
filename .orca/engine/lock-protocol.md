# Lock Protocol

Every orca-* skill must follow this protocol to prevent concurrent write sessions and expose the call stack to sub-skills at runtime. Skills are either **write** (exclusive) or **read-only** (concurrent).

- **Write skills:** breach, feed, ride, wash, therapy, meditate — acquire exclusive write access; block other write sessions
- **Read-only skills:** digest — register as a reader; never block and never blocked by write sessions

## Lock file — `.orca/.lock`

JSON shape:
```json
{
  "pid": 12345,
  "hostname": "my-laptop",
  "user": "bm",
  "acquired": "2026-03-24T14:30:00Z",
  "branch": "issue-42-short-title",
  "issue": "#42",
  "stack": ["orca-ride"],
  "readers": []
}
```

`stack` is an ordered list of write skill names from outermost (root) to innermost (current sub-skill). The root write skill's name is always `stack[0]`.

`readers` is a list of active read-only sessions. Each entry: `{"skill": "orca-digest", "pid": 12345, "hostname": "my-laptop", "user": "bm", "acquired": "..."}`.

## Obtaining hostname, user, pid, and timestamp

To obtain the four values needed for the lock file, run this single Python command — it works on Windows, macOS, and Linux and does not trigger Claude Code permission prompts:

```bash
python3 -c "import socket, os, getpass, datetime; print(socket.gethostname(), getpass.getuser(), os.getpid(), datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
```

Output is space-separated on one line: `<hostname> <user> <pid> <timestamp>`. Read the four values from this output and use them when writing the lock JSON. Never use `hostname`, `whoami`, `echo $$`, or `date` to obtain these values — those commands trigger Claude Code permission prompts on some platforms.

## Write skill startup

Applies to: breach, feed, ride, wash, therapy, meditate.

1. Try to read `.orca/.lock` using the Read tool.
2. **File does not exist** → write a new lock: run the Python command above to obtain hostname, user, pid, and UTC timestamp; also get the current git branch and issue context; write the JSON to `.orca/.lock` using the Write tool with `stack` containing only this skill's name and `readers: []`.
3. **File exists, different hostname or user** → hard abort. Show the lock contents and say: "Another orca session is running on a different machine or as a different user. Resolve that session before starting a new one."
4. **File exists, same hostname and user, `stack` is non-empty** → check whether the recorded process is still running. If the process is no longer running (stale): show the lock contents and ask "Found a stale lock from `<acquired>` — clear it and continue? (y/n)". If yes: overwrite with a fresh lock (preserve existing `readers`). If no: abort.
5. **File exists, same hostname and user, process still running** → hard abort. Show the lock contents and say: "A write orca session is already running on this machine — only one write session at a time."
6. **File exists, `stack` is empty** → a read-only session is registered but no write session is active. Acquire write access: set `stack` to contain only this skill's name; preserve `readers`; write the updated JSON back.

## Write skill exit

The write skill that set `stack[0]` is the one that clears it. When `stack` contains only your own name (all sub-skills have exited):
- If `readers` is empty → delete `.orca/.lock`
- If `readers` is non-empty → clear `stack` to `[]` and write the updated JSON back (leave the lock for readers to clean up)

## Read-only skill startup

Applies to: digest.

1. Try to read `.orca/.lock` using the Read tool.
2. **File does not exist** → write a new lock: run the Python command above to obtain hostname, user, pid, and UTC timestamp; write the JSON with `stack: []` and `readers` containing this session's entry.
3. **File exists, different hostname or user** → hard abort. Show the lock contents and say: "An orca session is running on a different machine or as a different user. Resolve that session before starting a new one."
4. **File exists, same hostname and user** → append this session's entry to `readers` (using the Python command above to obtain pid, hostname, user, and acquired timestamp for the entry); write the updated JSON back. Proceed regardless of `stack` state — read-only sessions never block on write sessions.

## Read-only skill exit

1. Read `.orca/.lock` using the Read tool.
2. Remove this session's entry from `readers`.
3. If `stack` is empty and `readers` is now empty → delete `.orca/.lock`.
4. Otherwise → write the updated JSON back.

## Sub-skill entry

Applies to: sing, lasso — and any write skill invoked by another write skill.

1. Read `.orca/.lock` using the Read tool.
2. Append this skill's name to `stack`.
3. Write the updated JSON back using the Write tool.

## Sub-skill exit

1. Read `.orca/.lock` using the Read tool.
2. Remove this skill's name from `stack` (pop the last entry — your own name).
3. Write the updated JSON back using the Write tool.
4. Do NOT delete the lock file — the root skill owns deletion.

## Read-only sub-skill entry

Applies to: a normally-write skill invoked from within a read-only session that makes no local file changes or git operations in that context. Currently: orca-feed when called from orca-digest (GitHub API calls only; no PRD update, no git commands).

A skill is in read-only sub-skill context when `.orca/.lock` shows `stack` is empty AND `readers` contains an `orca-digest` entry.

1. Read `.orca/.lock` using the Read tool.
2. If `stack` is empty and `readers` contains an `orca-digest` entry → append this skill's entry to `readers`; write the updated JSON back. Proceed in read-only mode — skip any steps that modify local files or run git commands.
3. Otherwise → follow the standard write skill startup protocol.

## Read-only sub-skill exit

1. Read `.orca/.lock` using the Read tool.
2. Remove this skill's entry from `readers`.
3. If `stack` is empty and `readers` is now empty → delete `.orca/.lock`.
4. Otherwise → write the updated JSON back.

## Reading the stack

Any skill can read `.orca/.lock` to inspect `stack` and `readers` and adjust behaviour based on who called it. Example: orca-therapy skips the "implement now or file as issue?" mode selection when `stack[0]` is `orca-ride` — the caller already determined the mode.
