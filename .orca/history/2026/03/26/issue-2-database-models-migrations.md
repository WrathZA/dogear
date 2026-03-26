## Issue #2 — Database models + Alembic migrations (DONE, closed)
https://github.com/WrathZA/dogear/issues/2

Closed: 2026-03-26
Commit: 888ef60
Security: clean
Skill-judge: not applicable
PRD sections: Domain objects (Bookmark, Tag, TaskConfig), Deployment (DATABASE_URL env var), Testing Decisions

- Chose `String(36)` for UUID PKs rather than a native UUID type — SQLite has no UUID column type; string is portable and readable in DB browsers without tooling
- Chose `lazy="selectin"` for the Bookmark↔Tag relationship to avoid N+1 queries on list endpoints; selectin loads related tags in a second query per batch rather than per row
- Placed `bookmark_tags` join table in `bookmark.py` (not a separate file) — it has no model class of its own; living with `Bookmark` keeps the FK references close to the owning side
- Wired Alembic `env.py` to use `async_engine_from_config` + `connection.run_sync` pattern — standard approach for async SQLAlchemy; avoids the "greenlet" error that occurs when running sync migrations against an async engine
- `DATABASE_URL` is overridden via `config.set_main_option` in `env.py` (not just `alembic.ini`) — ensures the env var is respected regardless of how alembic is invoked
- Added `pytest.ini` with `asyncio_mode=auto` and `asyncio_default_fixture_loop_scope=function` — suppresses pytest-asyncio deprecation warning about loop scope; makes all async tests discoverable without `@pytest.mark.asyncio` decoration
- All acceptance criteria met; issue closed
