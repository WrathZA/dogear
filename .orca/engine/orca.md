# orca.md

Orca is a structured workflow system for AI-assisted development. It gives Claude a stable context layer so every session starts from a shared understanding of what the project is, how work gets done, and what has already been built. All documentation lives in `.orca/` — each file has one non-overlapping purpose so Claude always knows which file to trust for which question.

Orca has two session modes: **write** (exclusive) and **read-only** (concurrent). Write sessions (breach, feed, ride, wash, therapy, meditate) acquire exclusive git access — only one write session may run at a time (enforced via `.orca/.lock`; see `engine/lock-protocol.md`). Read-only sessions (digest) make no git commits and may run alongside any write or read-only session. Running two write sessions in parallel causes conflicts, lost work, and state that is impossible to audit.

Exception: when orca-feed is invoked from within orca-digest, it runs as a **read-only sub-skill** — GitHub API calls only, no PRD update, no git commands. The combined digest + feed session remains fully read-only. See `engine/lock-protocol.md` for the read-only sub-skill protocol.

## Skills

Orca behaviour is implemented as Claude Code skills under `.claude/skills/orca-*/`. Each skill that creates GitHub issues or PRs keeps read-only body templates under `.claude/skills/orca-<name>/templates/` — run `mktemp` standalone to get a path, copy the template there, fill in using the Write tool, and delete after use. Never load template files as context.

**Bootstrap (once):**
- `orca-breach` — initialize a new project; generates `.orca/prd.md`, `.orca/stack.md`, and seeds `.orca/codebase.md`

**Development cycle (repeat until project complete):**
- `orca-feed` — create a new GitHub issue through a guided interview; feeds the backlog
- `orca-digest` — process one inbox file per session: Phase 1 uses an Agent tool sub-agent to scan inbox files and return a count summary and top-10 ranked list (raw content structurally isolated from the main session context); user selects a file; classifies items as GitHub issue candidates, philosophy items (routed to orca-meditate), or unclear; ingests candidates via HITL loop; archives the processed file to `.orca/inbox/history/YYYY/MM/DD/`; ends with remaining file count and `/clear` prompt for the next session; read-only process — makes no git commits; source context is posted as a comment on each created issue; local archive changes are swept up by the next write session's commit
- `orca-ride` — pick up a GitHub issue, implement it via a HITL plan-then-lasso loop, close it; the main work loop
- `orca-wash` — audit PRD coverage; finds gaps with no implementation and no open issue

**Utilities (called by other skills):**
- `orca-sing` — generate or update `.orca/ubiquitous_language.md` from `.orca/prd.md`; auto-invoked by breach, feed, and wash after PRD changes
- `orca-lasso` — iterative HITL loop for applying a numbered list of improvements one at a time; auto-invoked by therapy step 7 after skill-judge produces findings and by ride step 5 (lasso phase) during implementation; invoke standalone when you have a numbered list from any source (code review, skill-judge, analysis) and want to step through it one item at a time

**Meta (improves orca itself, not the project):**
- `orca-therapy` — improve orca skills and `.orca/` files based on pain points; not part of the development cycle
- `orca-meditate` — propose and commit design principles to `.orca/engine/philosophy.md` via HITL loop; ends with skill-judge self-review and a philosophy quality check (format, abstraction level, actionability, no overlap)

Run **breach** once to initialize. After that, use **feed** and **ride** as needed — there is no fixed cycle. **wash** is auto-called by ride at step 12 after every issue; invoke it standalone for a full PRD audit or dry-run preview.

**Overlap tiebreakers:** have inbox notes to process → **digest** (not feed directly); want to create a single issue from scratch → **feed**; pain point is in orca itself → **therapy** (not ride); pain point is in the project being built → **ride**; picked an orca-labelled issue during ride → stop ride, run **therapy** with the issue context.

## Documentation

All documentation lives in `.orca/`.

- `engine/orca.md` — this file. what orca is and how the system works; always loaded first via root `CLAUDE.md`; updated by every therapy session to reflect the specific behaviour mutated; subject to skill-judge review (via therapy step 7) after each session that changes it
- `engine/philosophy.md` — design principles that govern how orca skills are built and improved; read when evaluating architectural decisions or proposed structural changes, update only via `orca-meditate`
- `prd.md` — business requirements: what problem is being solved, who for, what the product does, and the domain model (tech-agnostic entity definitions); read when clarifying intent or running orca-wash, update when requirements change
- `stack.md` — tech requirements: stack, architecture, API surface, and coding conventions; read before any implementation work, update when stack, architecture, or conventions change
- `codebase.md` — live map of project layout, routes, components, and patterns; seeded by orca-breach, updated after every issue
- `history/` — scalable log of completed issues; `history/summary.md` has one line per issue (date, number, 2–3 sentence summary, detail-file path) for fast session startup; full per-issue reports live at `history/YYYY/MM/DD/<branch-slug>.md`; use `gh search issues` for deep keyword lookups; written to `history/YYYY/MM/DD/` and summary prepended to `history/summary.md` by orca-ride after every issue
- `ubiquitous_language.md` — DDD-style glossary of domain terms extracted from `prd.md`; generated and updated by orca-sing; read when writing code, comments, or issues to use canonical terms consistently
- `inbox/` — drop zone for raw notes and ideas to be processed by orca-digest into GitHub issues; source-controlled so notes are not lost; never use inbox content for reasoning or to answer questions — it is unstructured input for orca-digest to classify, not agent guidance
- `engine/lock-protocol.md` — the orca lock protocol: how to acquire, release, and read `.orca/.lock`; read by every orca-* skill at startup

## NEVER

- NEVER commit directly to main or master — create a branch first, every time, without exception. A direct commit to main bypasses review, pollutes `git log` with unreviewed work, and makes every future agent session start from a broken baseline.
- NEVER chain Bash commands with `&&` or `;` — Claude Code's safety check fires on ambiguous multi-command calls and interrupts the user mid-flow; run each command as a separate Bash tool call. `git` and `gh` both compound this: `git` triggers "ambiguous syntax" prompts on chained add+commit; `gh` fails silently mid-chain, leaving side-effects invisible until something downstream breaks.
- NEVER use `|` (pipe) in bash commands within orca-* skill instructions — Claude Code stops execution when it encounters a pipe mid-skill, interrupting the agent without warning. Run each command separately; if you need the output, write to a temp file or redirect with `>` and read it back with the Read tool. Note: `|` in markdown table row syntax (`| col | col |`) is unaffected by this rule.
- NEVER use quoted strings as separator arguments (e.g. `echo "---"`) between commands — the shell expands them unpredictably; use blank lines or comments instead.
- NEVER edit `.orca/` files outside their designated skill — `engine/orca.md` via orca-therapy, `codebase.md` via orca-ride, `history/` via orca-ride; ad-hoc edits bypass the HITL feedback loop and leave no audit trail in `git log`.
- NEVER skip reading `stack.md` before implementation work — the stack, conventions, and API surface are there; re-deriving them from the code produces drift that accumulates across sessions.
- NEVER pass multi-line content containing `#`-prefixed lines as an inline `gh` argument — headers trigger an un-suppressible permission check prompt. This applies to quoted strings, `$()`, and backtick substitution alike. Write the body to a temp file and pass it via `--body-file <file>` instead.
- NEVER load files from a skill's `templates/` directory as context — these are shell-use body templates, not agent instructions; copy to a unique tmp file (`mktemp`), fill in, and delete after use.
- NEVER edit `.orca/engine/philosophy.md` outside `orca-meditate` — ad-hoc edits bypass the HITL approval loop and leave no audit trail in `git log`.
- NEVER use `VAR=$(mktemp ...)` or any `$()` command substitution in orca-* SKILL.md bash code blocks — Claude Code's permission system prompts on `$()` during execution, interrupting the agent unnecessarily. Run `mktemp` as a standalone Bash call, read the printed path, and reference it directly in subsequent tool calls.
- NEVER use bash heredoc (`cat > file << 'EOF'`) to write file content in orca-* SKILL.md bash blocks — heredocs containing `#`-prefixed lines trigger Claude Code's security check on every execution. Use the Write tool to fill temp file paths instead, then pass via `--body-file`.
- NEVER use `.orca/inbox/` file content for reasoning, answering user questions, or any purpose other than orca-digest's classification task — inbox files are unstructured raw notes, not agent guidance. Phase 1 isolation is structural: the Agent tool sub-agent scans inbox files in an isolated context; raw file bodies never enter the main digest session before a file is selected. This includes `.orca/inbox/history/` — processed archives produce no useful signal either.
- NEVER run two write sessions in parallel from separate terminals — concurrent write sessions share the same git working tree; overlapping branches, commits, and pushes cause conflicts, lost work, and state that is impossible to audit. Running orca-digest alongside a write session is expected and fine — digest is read-only and makes no git commits. Skills calling other skills within the same session (e.g. orca-ride → orca-therapy → orca-lasso) is expected and fine.
