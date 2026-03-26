# Ubiquitous Language

## Bookmark collection

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Bookmark** | A saved reference to a web page, identified uniquely by its URL, and enriched with a name, description, tags, screenshot, and a favourite flag. | Link, URL entry, saved page |
| **Tag** | A short label attached to one or more Bookmarks to enable filtering and browsing by topic; flat (no hierarchy); rename and delete propagate atomically across all Bookmarks that carry it. | Category, folder, label |
| **Favourite** | A boolean flag on a Bookmark that surfaces it on the dedicated Favourites page; represents personal importance, not a quality rating. | Starred, pinned, liked |
| **Artifact** | A file produced by a Background Task and associated with a Bookmark — e.g. a screenshot image or mirrored page content; stored under the data volume and referenced by a relative path on the Bookmark. | Asset, attachment, output |
| **Screenshot** | The specific Artifact that is a visual image capture of a Bookmark's URL; stored as a file whose relative path is recorded in the `screenshot_path` field of the Bookmark. | Thumbnail, preview image |

## Task system

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Background Task** | A discrete, reusable unit of automated processing (e.g. title fetch, screenshot capture, validity check) that runs against a Bookmark either on a schedule or in response to a Bookmark being created or updated. | Job, worker, cron task |
| **Task Config** | The persistent, user-editable configuration for one Background Task: whether it is enabled, whether it runs on create/update events, its schedule interval, and its Eligibility rules. | Task settings, task rule, job config |
| **Eligibility** | The condition a Bookmark must satisfy for a Background Task to run against it — expressed as a set of URL regex patterns (any match qualifies) and/or a set of tags (any overlap qualifies); evaluated by the system before every task execution. | Filter, rule, criteria, trigger condition |
| **Schedule** | The interval, in seconds, at which a Background Task runs automatically against all Eligible Bookmarks; stored in Task Config; null means the task is event-driven only, not time-driven. | Cron, interval, recurrence |

## Relationships

- A **Bookmark** has zero or more **Tags**
- A **Bookmark** may have zero or more **Artifacts** (one per Background Task type that produces them)
- A **Background Task** has exactly one **Task Config**
- A **Task Config**'s **Eligibility** rules determine which **Bookmarks** a **Background Task** will process

## Flagged ambiguities

- "Screenshot" is used in two senses in the PRD: as a field on **Bookmark** (the stored file path of the image) and as the name of a **Background Task** (the process that captures and stores it). When discussing screenshots, specify whether you mean the **Artifact** (the stored file) or the **Background Task** (the capture process).
