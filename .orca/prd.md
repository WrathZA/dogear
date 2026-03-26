# bookmark-it PRD

## Problem Statement

Personal bookmark management using browser-native bookmarks is brittle: bookmarks are tied to a specific browser profile, offer no metadata beyond a title and folder, provide no way to verify links are still alive, and cannot be easily searched across tags, descriptions, or full-text. Users who collect large numbers of bookmarks lose the ability to rediscover them over time. There is no simple self-hosted tool that combines a clean browsable UI, rich metadata, tag-based organisation, and extensible background processing (validity checks, screenshots, mirroring) in a single deployable container.

## Solution

bookmark-it is a self-hosted, single-container web application for managing a personal collection of bookmarks. It provides a searchable, filterable, paginated list of bookmarks with rich metadata (name, description, tags, screenshot, favourite flag). State — search query, tag filters, sort order, page — is encoded in the URL so every view is deep-linkable. A background task system runs tasks on a schedule or in response to bookmark create/update events; tasks decide eligibility based on user-configured URL regex patterns or tag matches. All data and artifacts are stored in a mounted volume so the container is stateless and replaceable.

## User Stories

### Browsing and discovery
1. As a user, I want to see a paginated list of all my bookmarks on the main page, so that I can browse my collection.
2. As a user, I want to search bookmarks by keyword across URL, name, description, and tags, so that I can find a bookmark without knowing exactly where I filed it.
3. As a user, I want to filter bookmarks by one or more tags, so that I can browse a specific topic.
4. As a user, I want to specify tag filters in the URL (e.g. `?tags=python,dev`), so that I can share or bookmark a pre-filtered view.
5. As a user, I want to sort bookmarks by name, URL, date added, or date updated in ascending or descending order, so that I can organise the list the way I prefer.
6. As a user, I want the search query, tag filters, sort order, and page number to be reflected in the URL, so that refreshing the page or sharing a link preserves the exact view.
7. As a user, I want to paginate through bookmarks, so that large collections do not overwhelm the page.
8. As a user, I want to see a dedicated Favourites page that lists only bookmarks I have marked as favourite, so that I can quickly reach my most-used links.
9. As a user, I want each bookmark card in the list to show the screenshot thumbnail (if available), name, URL, description, tags, and favourite indicator, so that I can identify a bookmark at a glance.
10. As a user, I want to toggle dark/light mode, so that I can use the app comfortably in different lighting conditions.
11. As a user, I want a persistent left-side navigation menu with labelled icons for All Bookmarks, Favourites, Tags, Add New, and Task Config, so that I can move between sections without hunting for links.

### Bookmark management
12. As a user, I want to add a new bookmark by providing only a URL, so that the minimum friction to save a link is as low as possible.
13. As a user, I want the bookmark name to be automatically fetched from the page `<title>` in the background after saving, so that I do not have to wait for the network request to complete before the bookmark is saved.
14. As a user, I want to optionally provide a name, description, tags, and favourite flag when adding a bookmark, so that I can enrich the record immediately if I choose.
15. As a user, I want submitting a URL that already exists in the system to overwrite the existing bookmark with the new data, so that I do not receive an error and can easily update a record.
16. As a user, I want to edit any field of an existing bookmark, so that I can correct or enrich metadata over time.
17. As a user, I want to delete a bookmark, so that I can remove links I no longer need.
18. As a user, I want to toggle the favourite flag directly from the bookmark list without opening the detail page, so that I can quickly mark or unmark favourites.
19. As a user, I want a bookmark detail/edit page at a stable URL, so that I can link directly to the full record of a bookmark.

### Tag management
20. As a user, I want to see a Tags page listing all tags in use with their bookmark counts, so that I can understand how my collection is organised.
21. As a user, I want to rename a tag across all bookmarks that use it, so that I can correct a typo or consolidate two tags without editing each bookmark individually.
22. As a user, I want to delete a tag, which removes it from all bookmarks that carry it, so that I can clean up stale or unused tags.
23. As a user, I want to see how many bookmarks use each tag on the Tags page, so that I can identify which tags are most active.

### Background task system
24. As a user, I want background tasks to run automatically on a configured schedule (e.g. daily validity check), so that I do not have to trigger maintenance manually.
25. As a user, I want background tasks to run automatically when a bookmark is created or updated, subject to each task's eligibility rules, so that newly added bookmarks are processed without manual intervention.
26. As a user, I want to manually trigger a specific background task for a single bookmark from the UI, so that I can force-run a task on demand.
27. As a user, I want to manually trigger all applicable background tasks for a single bookmark, so that I can refresh all metadata at once.
28. As a user, I want each task to have a user-configurable set of URL regex patterns and tags that determine whether it runs for a given bookmark, so that tasks only fire for relevant bookmarks.
29. As a user, I want to configure task eligibility rules (URL regex, tags, schedule interval, enabled/disabled) via a Task Config page in the UI, so that I do not need to edit code or config files.
30. As a user, I want task configuration to persist across container restarts, so that I do not have to reconfigure tasks after a redeploy.
31. As a user, I want the system to be extensible so that a developer can add a new background task by implementing a standard interface, so that the feature set can grow without large structural changes.

### Deployment and data
32. As a user, I want the entire application to run in a single Docker container, so that deployment requires only one `docker run` command.
33. As a user, I want the SQLite database and all artifacts (screenshots, mirrored content) to be stored in a mounted host volume, so that my data survives container replacement or upgrade.
34. As a user, I want the database file path to be configurable via an environment variable, so that I can point the container at a demo database or a production database without rebuilding the image.
35. As a user, I want a demo seed script that populates 20 popular bookmarks with 4 marked as favourites, so that I can evaluate the UI without manually entering data.

## Implementation Decisions

### Domain objects

**Bookmark**
- `id` — UUID, primary key
- `url` — string, unique, required
- `name` — string, nullable (filled by background title-fetch task if not provided)
- `description` — text, nullable
- `screenshot_path` — string, nullable (relative path within the artifacts volume)
- `favourite` — boolean, default false
- `created_at` — datetime
- `updated_at` — datetime

**Tag**
- Tags are stored as a many-to-many relationship between bookmarks and a `Tag` table (`id`, `name` unique). This enables rename and delete operations to propagate atomically without scanning bookmark JSON fields.

**TaskConfig**
- `id` — UUID, primary key
- `task_name` — string, unique (matches the registered task identifier)
- `enabled` — boolean
- `run_on_create` — boolean
- `run_on_update` — boolean
- `url_patterns` — JSON array of regex strings
- `tags` — JSON array of tag strings
- `schedule_interval_seconds` — integer, nullable (null = not scheduled)

### Modules

**BookmarkRepository** — all database reads and writes for bookmarks; exposes search (full-text across url/name/description/tags), filter by tags, sort by field+direction, paginate; upserts on duplicate URL.

**TagRepository** — aggregates tags from the bookmark↔tag join; rename propagates atomically; delete removes the tag from all bookmarks.

**TaskRegistry** — a singleton that holds references to all registered `BackgroundTask` implementations; tasks self-register on import; provides lookup by name.

**BackgroundTask interface** — each task implements: `name: str`, `description: str`, `run(bookmark) -> None`; eligibility is resolved externally by TaskRunner against TaskConfig.

**TaskRunner** — loads TaskConfig for a given task, evaluates URL regex and tag conditions against the bookmark, executes the task in an asyncio background coroutine; called by API handlers on create/update and by the manual trigger endpoint.

**Scheduler** — APScheduler instance integrated into the FastAPI lifespan; on startup reads all TaskConfigs with `schedule_interval_seconds` set and schedules them; reschedules when TaskConfig is updated.

**API layer (FastAPI)**
- `GET /api/bookmarks` — query params: `search`, `tags` (comma-separated), `sort` (field:direction), `page`, `page_size`
- `GET /api/bookmarks/{id}`
- `POST /api/bookmarks` — upserts on duplicate URL; fires eligible on-create tasks in background
- `PUT /api/bookmarks/{id}` — fires eligible on-update tasks in background
- `DELETE /api/bookmarks/{id}`
- `GET /api/bookmarks/exists?url=` — returns `{exists: bool, id?: uuid}`
- `GET /api/tags`
- `PUT /api/tags/{name}/rename` — body: `{new_name: str}`
- `DELETE /api/tags/{name}`
- `GET /api/task-configs` — list all task configurations
- `PUT /api/task-configs/{task_name}` — update a task's configuration
- `POST /api/tasks/run/{task_name}/{bookmark_id}` — manual single-task trigger
- `POST /api/tasks/run_all/{bookmark_id}` — manual all-applicable-tasks trigger

**Frontend (Next.js/React)**
- URL params are the single source of truth for list state (search, tags, sort, page)
- `BookmarkList` — fetches `/api/bookmarks` with params derived from URL; renders `BookmarkCard` grid; manages `PaginationControls`
- `BookmarkCard` — shows thumbnail, name, URL, description, tags, favourite toggle (inline PATCH)
- `BookmarkForm` — shared add/edit form; on submit calls POST (new) or PUT (edit)
- `FavouritesPage` — calls `/api/bookmarks?favourite=true`
- `TagsPage` — lists tags with counts; rename and delete inline
- `TaskConfigPage` — lists registered tasks; per-task form for eligibility rules and schedule
- `SideNavigation` — persistent left drawer with route links and `ThemeToggle`

### Deployment
- Single `Dockerfile` — Python + Node in one image; builds Next.js static output; serves it via the FastAPI static-files mount or a lightweight static server managed by supervisord
- supervisord manages: uvicorn (FastAPI + APScheduler lifespan), Next.js production server
- Volume mount point: `/app/data` — contains `bookmarks.db` and `artifacts/`
- `DATABASE_URL` env var controls SQLite path; defaults to `/app/data/bookmarks.db`

## Testing Decisions

A good test verifies observable behaviour through the module's public interface — it does not assert on internal state, private methods, or implementation details. Tests should remain valid if the internals are refactored without changing behaviour.

**Modules to test:**
- `BookmarkRepository` — search, filter, sort, paginate, upsert-on-duplicate behaviour; tested against a real in-memory SQLite instance (not mocked)
- `TagRepository` — rename propagation across bookmarks, delete propagation; real in-memory SQLite
- `TaskRunner` — eligibility evaluation (URL regex match, tag match, combined); bookmark stub passed in; no network calls
- FastAPI API routes — integration tests using `httpx` + FastAPI `TestClient`; cover happy paths, 404s, validation errors, and duplicate-URL upsert

## Out of Scope

- Multi-user accounts, authentication, or authorisation — this is a single-user personal tool
- Import from browser bookmark files (HTML export) — v1 only
- Full-text content indexing of bookmarked pages — validity check and mirroring are background tasks but indexing page bodies is not included
- Mobile-native app — the web UI should be responsive but there is no native app
- Notifications or alerting when a validity check fails — v1 only stores the result; no email/push
- Tag hierarchies or nested tags — flat tag list only

## Further Notes

- The `GET /api/bookmarks/exists` endpoint is intended for use by a browser extension or external tool that wants to check before attempting to add a duplicate.
- The demo seed script should be a standalone Python script (`scripts/seed_demo.py`) runnable inside or outside the container.
- Alembic migrations should be included from the start so schema changes across versions can be applied to existing data volumes without data loss.
- The `screenshot_path` field stores a path relative to the artifacts volume root (`/app/data/artifacts`), not an absolute path, so the path remains valid if the container is recreated with a different host mount point.
- APScheduler should use the SQLite job store (same database) so scheduled tasks survive container restarts without reconfiguration.
