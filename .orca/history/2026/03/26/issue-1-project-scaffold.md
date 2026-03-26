## Issue #1 — Project scaffold + Docker skeleton (DONE, closed)
https://github.com/WrathZA/dogear/issues/1

Closed: 2026-03-26
Commit: be69e6f
Security: clean (removed unused `waitress` install from Dockerfile)
Skill-judge: not applicable

PRD sections: Deployment and data (user stories 10, 11, 32, 33, 34)

- Used `python3 -m http.server` for the static file server instead of a dedicated server (waitress/nginx) — acceptable for a local-network-only single-user deployment; removes an extra dependency
- Chose `corepack prepare pnpm@10.32.1 --activate` in Dockerfile rather than `npm install -g pnpm` — corepack is the Node-native package manager manager; avoids global npm state
- `DATABASE_URL` default set to `sqlite+aiosqlite:////app/data/bookmarks.db` at both the Python module level and in the Dockerfile ENV — the module-level default handles `python -m pytest` runs outside the container without needing the env var set
- ThemeToggle persists via `localStorage` + a `body.dark` CSS class with `filter: invert(1) hue-rotate(180deg)` — the 98.css approach; no separate theme context needed at scaffold stage
- PRD mentions "Next.js" in the Implementation Decisions frontend section but `stack.md` and the issue both say Vite — used Vite per `stack.md` which governs tech choices
- All acceptance criteria met; issue closed
