# Codebase: bookmark-it

> Seeded by orca-breach. Updated by orca-ride after each issue.

## Repository root

```
bookmark-it/
├── backend/
├── frontend/
├── scripts/
├── Dockerfile
├── supervisord.conf
├── docker-compose.yml
└── .orca/
```

## Backend (`backend/`)

Python 3.12 + FastAPI application. Entry point: `backend/app/main.py`.

Files marked ✓ exist; unmarked are planned (not yet implemented).

```
backend/
├── app/
│   ├── main.py ✓            # FastAPI app with GET /health; lifespan + routers to be added in later issues
│   ├── database.py ✓        # SQLAlchemy async engine + session factory; DATABASE_URL from env (default /app/data/bookmarks.db)
│   ├── routes/              # (planned — issue #3, #4)
│   ├── services/            # (planned — issue #3, #4)
│   ├── repositories/        # (planned — issue #3, #4)
│   ├── models/ ✓            # SQLAlchemy ORM models (issue #2)
│   │   ├── bookmark.py ✓    # Bookmark model + bookmark_tags join table (many-to-many)
│   │   ├── tag.py ✓         # Tag model; back-ref to Bookmark via bookmark_tags
│   │   ├── task_config.py ✓ # TaskConfig model; url_patterns + tags as JSON columns
│   │   └── __init__.py ✓    # Re-exports Bookmark, Tag, TaskConfig, bookmark_tags
│   ├── schemas/             # (planned — issue #3, #4)
│   ├── tasks/               # (planned — issue #3+)
│   └── scheduler.py         # (planned — issue #3+)
├── alembic/ ✓               # Alembic migrations (issue #2)
│   ├── env.py ✓             # Async engine wired via run_sync; imports all models for autogenerate
│   ├── script.py.mako ✓     # Default migration template
│   └── versions/ ✓
│       └── 47f1282d4645_initial_schema.py ✓  # Creates bookmarks, tags, task_configs, bookmark_tags
├── alembic.ini ✓            # script_location=alembic; sqlalchemy.url overridden at runtime by DATABASE_URL
├── pytest.ini ✓             # asyncio_mode=auto; loop_scope=function
├── tests/ ✓                 # (issue #2+)
│   ├── conftest.py ✓        # in-memory SQLite async session fixture (db_session)
│   └── unit/
│       └── test_models.py ✓ # 6 tests: import check + PRAGMA table_info per table
└── requirements.txt ✓       # fastapi, uvicorn, sqlalchemy, aiosqlite, alembic, apscheduler, httpx, pydantic, pytest, pytest-asyncio — all pinned
```

## Frontend (`frontend/`)

Vite + React 18 SPA. Styled with 98.css. Entry point: `frontend/src/main.tsx`.

Files marked ✓ exist; unmarked are planned (not yet implemented).

```
frontend/
├── src/
│   ├── main.tsx ✓           # React root; BrowserRouter + Routes; imports 98.css globally; app-shell layout
│   ├── index.css ✓          # App shell layout (flex, nav width); body.dark theme class
│   ├── pages/
│   │   ├── AllBookmarks.tsx ✓  # Stub — route "/" (full implementation: issue #5)
│   │   ├── Favourites.tsx ✓    # Stub — route "/favourites" (issue #6)
│   │   ├── Tags.tsx ✓          # Stub — route "/tags" (issue #7)
│   │   ├── AddNew.tsx ✓        # Stub — route "/add" (issue #6)
│   │   └── TaskConfig.tsx ✓    # Stub — route "/task-config" (issue #4+)
│   ├── components/
│   │   ├── SideNavigation.tsx ✓ # Persistent left nav: All Bookmarks, Favourites, Tags, Add New, Task Config; uses NavLink with active bold
│   │   ├── ThemeToggle.tsx ✓    # Light/dark toggle; persists to localStorage; toggles body.dark class
│   │   ├── BookmarkCard.tsx     # (planned — issue #5)
│   │   ├── BookmarkForm.tsx     # (planned — issue #6)
│   │   ├── PaginationControls.tsx # (planned — issue #5)
│   │   ├── SearchInput.tsx      # (planned — issue #5)
│   │   └── TagFilter.tsx        # (planned — issue #5)
│   ├── api/                     # (planned — issue #5+)
│   └── types.ts                 # (planned — issue #5+)
├── playwright/                  # (planned — issue #5+)
├── index.html ✓
├── vite.config.ts ✓             # @vitejs/plugin-react; proxy /api → localhost:8000
├── tsconfig.json ✓              # strict mode, noEmit, react-jsx
├── package.json ✓               # 98.css 0.1.19, react 18.3.1, react-router-dom 6.28.0, vite 6.0.5
└── pnpm-lock.yaml ✓
```

## Scripts (`scripts/`)

```
scripts/
└── seed_demo.py     # Inserts 20 popular bookmarks into the database; marks 4 as favourite
```

## Docker

```
Dockerfile           # Multi-stage: Node build stage (Vite), Python runtime stage; supervisord entrypoint
supervisord.conf     # Manages: uvicorn (FastAPI on :8000), static file server (Vite dist on :3000)
docker-compose.yml   # Maps host port, mounts /app/data volume, passes DATABASE_URL
```

## Data volume (`/app/data/`)

```
/app/data/
├── bookmarks.db          # SQLite database (path overridable via DATABASE_URL)
└── artifacts/            # Task outputs: screenshots, mirrored content; paths stored relative in DB
```

## Key patterns

- **Upsert on duplicate URL**: `BookmarkRepository.upsert()` uses SQLite `INSERT OR REPLACE` keyed on `url`
- **Task eligibility**: `TaskRunner` loads `TaskConfig` by task name, compiles `url_patterns` as regex list, checks any match against bookmark URL and tag intersection against bookmark tags
- **Background task interface**: all tasks extend `BackgroundTask`; implement `name: str`, `description: str`, `run(bookmark: Bookmark) -> None`; import in `tasks/__init__.py` triggers self-registration
- **URL-as-state**: `BookmarkList` reads/writes `useSearchParams`; no client state store; every list view is deep-linkable
