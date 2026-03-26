## Issue #3 — Bookmark CRUD API (DONE, closed)
https://github.com/WrathZA/dogear/issues/3

Closed: 2026-03-26
Commit: 6838bd6
Security: clean
Skill-judge: not applicable
PRD sections: Bookmark management (user stories 12–17), API layer, BookmarkRepository, BookmarkService

- Used direct join-table insert/delete for _sync_tags instead of mutating bookmark.tags relationship — accessing the relationship on a freshly-flushed-but-not-committed object triggers an async lazy-load (MissingGreenlet) with aiosqlite; the join-table approach avoids the ORM relationship entirely
- Registered GET /api/bookmarks/exists before /{bookmark_id} in the router — FastAPI matches routes in declaration order; putting /exists after /{id} would cause "exists" to be treated as a bookmark id
- `import app.models` after `from app.main import app` shadows the FastAPI instance with the package module; fixed by using `import app.models as _models` before the FastAPI import
- sort_field validated against a whitelist before getattr() to prevent attribute access on arbitrary Bookmark attributes
- All 38 tests pass (16 unit + 17 integration + 6 pre-existing model tests)
