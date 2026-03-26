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

```
backend/
├── app/
│   ├── main.py              # FastAPI app instantiation, lifespan (APScheduler start/stop), router registration
│   ├── routes/
│   │   ├── bookmarks.py     # GET/POST/PUT/DELETE /api/bookmarks, GET /api/bookmarks/exists
│   │   ├── tags.py          # GET /api/tags, PUT /api/tags/{name}/rename, DELETE /api/tags/{name}
│   │   └── tasks.py         # GET /api/task-configs, PUT /api/task-configs/{name}, POST /api/tasks/run/*
│   ├── services/
│   │   ├── bookmark_service.py   # Orchestrates BookmarkRepository; triggers TaskRunner on create/update
│   │   ├── tag_service.py        # Orchestrates TagRepository; rename and delete propagation
│   │   └── task_runner.py        # Loads TaskConfig, evaluates eligibility (URL regex + tags), dispatches task
│   ├── repositories/
│   │   ├── bookmark_repository.py  # SQLAlchemy async CRUD; search, filter, sort, paginate, upsert
│   │   └── tag_repository.py       # Tag aggregation, rename, delete across bookmark join table
│   ├── models/
│   │   ├── bookmark.py      # Bookmark ORM model (id, url, name, description, screenshot_path, favourite, timestamps)
│   │   ├── tag.py           # Tag ORM model (id, name); many-to-many join to Bookmark
│   │   └── task_config.py   # TaskConfig ORM model (task_name, enabled, run_on_create, run_on_update, url_patterns, tags, schedule_interval_seconds)
│   ├── schemas/
│   │   ├── bookmark.py      # BookmarkCreate, BookmarkUpdate, BookmarkResponse, PaginatedBookmarkResponse
│   │   ├── tag.py           # TagResponse, TagRenameRequest
│   │   └── task_config.py   # TaskConfigResponse, TaskConfigUpdate
│   ├── tasks/
│   │   ├── base.py          # BackgroundTask abstract base: name, description, run(bookmark)
│   │   ├── registry.py      # TaskRegistry singleton; tasks self-register on import
│   │   ├── title_fetch.py   # Fetches <title> from bookmark URL; fills name if blank
│   │   ├── screenshot.py    # Takes screenshot of bookmark URL; writes to /app/data/artifacts/
│   │   └── validity_check.py # HTTP HEAD request to verify URL is reachable; updates a status field
│   ├── scheduler.py         # APScheduler AsyncIOScheduler; loads TaskConfigs at startup; re-registers on config update
│   └── database.py          # SQLAlchemy async engine + session factory; DATABASE_URL from env
├── alembic/
│   ├── env.py
│   ├── versions/            # Migration scripts
│   └── alembic.ini
├── tests/
│   ├── unit/
│   │   ├── test_task_runner.py     # Eligibility logic: URL regex, tag matching
│   │   └── test_bookmark_repository.py  # Search, filter, sort, paginate, upsert
│   └── integration/
│       ├── test_bookmarks_api.py   # Full API routes via TestClient
│       └── test_tags_api.py
└── requirements.txt
```

## Frontend (`frontend/`)

Vite + React 18 SPA. Styled with 98.css. Entry point: `frontend/src/main.tsx`.

```
frontend/
├── src/
│   ├── main.tsx             # React root, router setup (React Router)
│   ├── pages/
│   │   ├── BookmarkList.tsx    # Main page; URL params drive search/filter/sort/page state
│   │   ├── Favourites.tsx      # Filtered view: favourite=true
│   │   ├── BookmarkDetail.tsx  # Add / edit form page (/bookmarks/new, /bookmarks/:id)
│   │   ├── Tags.tsx            # Tag list with counts; inline rename and delete
│   │   └── TaskConfig.tsx      # Per-task config: eligibility rules, schedule, enabled toggle
│   ├── components/
│   │   ├── SideNavigation.tsx  # Persistent left nav: All Bookmarks, Favourites, Tags, Add New, Task Config
│   │   ├── BookmarkCard.tsx    # Card: thumbnail, name, URL, description, tags, favourite toggle
│   │   ├── BookmarkForm.tsx    # Shared add/edit form fields
│   │   ├── PaginationControls.tsx
│   │   ├── SearchInput.tsx
│   │   ├── TagFilter.tsx       # Multi-tag filter chips
│   │   └── ThemeToggle.tsx     # Light/dark toggle
│   ├── api/
│   │   ├── bookmarks.ts     # Typed fetch wrappers for /api/bookmarks endpoints
│   │   ├── tags.ts          # Typed fetch wrappers for /api/tags endpoints
│   │   └── tasks.ts         # Typed fetch wrappers for /api/task-configs and /api/tasks endpoints
│   └── types.ts             # Shared TypeScript types mirroring API schemas
├── playwright/
│   └── tests/               # e2e test specs
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── pnpm-lock.yaml
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
