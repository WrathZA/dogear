# Stack: bookmark-it

## Constraints

- Deployment: local network only; single Docker container; no cloud providers
- Budget: $0 infrastructure cost — all compute on local hardware
- External integrations: none
- Single-user; no authentication required

## Tech Stack

- **Runtime (backend):** Python 3.12
- **Backend framework:** FastAPI with uvicorn
- **ORM:** SQLAlchemy 2.x (async) with Alembic for migrations
- **Background scheduling:** APScheduler 3.x with SQLite job store
- **Database:** SQLite; file path controlled by `DATABASE_URL` env var; default `/app/data/bookmarks.db`
- **Runtime (frontend):** Node.js 20 (build-time only)
- **Frontend framework:** React 18 + Vite (SPA, client-side rendering only)
- **UI styling:** 98.css (Windows 95/98 authentic chrome)
- **Frontend package manager:** pnpm (lockfile committed)
- **Python package manager:** pip with `requirements.txt` (committed)
- **Python formatter/linter:** Ruff
- **Process management:** supervisord (manages uvicorn + static file server within container)
- **Testing:** Pytest + httpx (backend unit + integration); Playwright (e2e)
- **Containerisation:** Single Docker image; `/app/data` volume for SQLite DB and artifacts

## Architecture

A single Docker container runs two processes under supervisord: uvicorn serving the FastAPI application (which hosts the background scheduler via APScheduler lifespan), and a static file server serving the pre-built Vite SPA. The SPA makes all data requests to the FastAPI REST API at `/api/*`. SQLite is the single database; APScheduler uses a SQLite job store in the same file to persist scheduled jobs across container restarts. When a bookmark is created or updated, the API handler enqueues applicable background tasks as asyncio background coroutines; each task checks its `TaskConfig` record to evaluate URL regex and tag eligibility before executing. Scheduled tasks are loaded from `TaskConfig` records on startup and re-registered whenever a config is updated. All persistent data — the SQLite file and artifact files (screenshots, mirrored content) — live under `/app/data`, which is a host-mounted volume.

## Project Layout

```
bookmark-it/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan, APScheduler init
│   │   ├── routes/              # One module per resource: bookmarks, tags, tasks
│   │   ├── services/            # Business logic: BookmarkService, TagService, TaskRunner
│   │   ├── repositories/        # DB access: BookmarkRepository, TagRepository
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── tasks/               # BackgroundTask implementations + TaskRegistry
│   │   └── scheduler.py         # APScheduler setup and job registration
│   ├── alembic/                 # Migrations
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # BookmarkList, Favourites, Tags, TaskConfig
│   │   ├── components/          # BookmarkCard, BookmarkForm, SideNavigation, ThemeToggle
│   │   ├── api/                 # Typed fetch wrappers per API endpoint
│   │   └── main.tsx
│   ├── playwright/              # e2e tests
│   ├── package.json
│   └── pnpm-lock.yaml
├── scripts/
│   └── seed_demo.py             # Populates 20 demo bookmarks, 4 marked favourite
├── Dockerfile
├── supervisord.conf
└── docker-compose.yml           # Convenience wrapper for local dev
```

## Conventions

- **Code organisation:** Layered — routes call services, services call repositories; no repository calls directly from routes
- **Error handling:** Python exceptions throughout; FastAPI exception handlers map domain exceptions to HTTP status codes; no Result/Either pattern
- **Async pattern:** `async/await` throughout FastAPI routes and repositories; APScheduler task functions are synchronous (APScheduler manages its own thread pool)
- **Type hints:** All Python functions fully type-hinted; Pydantic models for all API request and response bodies
- **TypeScript:** Strict mode enabled; `type` preferred over `interface` for object shapes; no `any`
- **React:** Functional components only; URL search params (`useSearchParams`) are the sole source of truth for list filter/sort/page state — no separate state library
- **Exports:** Named exports only (frontend); no barrel files
- **Lockfiles:** Both `requirements.txt` and `pnpm-lock.yaml` committed

## Development Commands

```
test (backend):    pytest
test (e2e):        pnpm --prefix frontend playwright test
format (backend):  ruff format backend/ && ruff check --fix backend/
format (frontend): pnpm --prefix frontend prettier --write src/
```

## Interface

### Bookmarks
- `GET /api/bookmarks?search=&tags=&sort=&page=&page_size=&favourite=` → paginated bookmark list
- `GET /api/bookmarks/{id}` → single bookmark
- `POST /api/bookmarks` → create or upsert bookmark (duplicate URL overwrites existing)
- `PUT /api/bookmarks/{id}` → update bookmark; fires eligible on-update tasks in background
- `DELETE /api/bookmarks/{id}` → delete bookmark
- `GET /api/bookmarks/exists?url=` → `{exists: bool, id?: uuid}`

### Tags
- `GET /api/tags` → list of `{name, count}` objects
- `PUT /api/tags/{name}/rename` → rename tag across all bookmarks; body: `{new_name: str}`
- `DELETE /api/tags/{name}` → remove tag from all bookmarks

### Background tasks
- `GET /api/task-configs` → list all registered task configurations
- `PUT /api/task-configs/{task_name}` → update task config (eligibility rules, schedule, enabled)
- `POST /api/tasks/run/{task_name}/{bookmark_id}` → manually trigger one task for one bookmark
- `POST /api/tasks/run_all/{bookmark_id}` → trigger all applicable tasks for one bookmark
