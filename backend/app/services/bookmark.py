from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark
from app.repositories.bookmark import BookmarkRepository
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    PaginatedBookmarkResponse,
)


class BookmarkNotFound(Exception):
    pass


def _to_response(bookmark: Bookmark) -> BookmarkResponse:
    return BookmarkResponse(
        id=bookmark.id,
        url=bookmark.url,
        name=bookmark.name,
        description=bookmark.description,
        screenshot_path=bookmark.screenshot_path,
        favourite=bookmark.favourite,
        tags=[t.name for t in bookmark.tags],
        created_at=bookmark.created_at,
        updated_at=bookmark.updated_at,
    )


class BookmarkService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = BookmarkRepository(session)

    async def create_or_update(self, data: BookmarkCreate) -> BookmarkResponse:
        bookmark = await self._repo.upsert(
            url=data.url,
            name=data.name,
            description=data.description,
            tags=data.tags,
            favourite=data.favourite,
        )
        return _to_response(bookmark)

    async def get(self, bookmark_id: str) -> BookmarkResponse:
        bookmark = await self._repo.get_by_id(bookmark_id)
        if bookmark is None:
            raise BookmarkNotFound(bookmark_id)
        return _to_response(bookmark)

    async def update(self, bookmark_id: str, data: BookmarkUpdate) -> BookmarkResponse:
        fields = data.model_dump(exclude_none=True)
        bookmark = await self._repo.update(bookmark_id, **fields)
        if bookmark is None:
            raise BookmarkNotFound(bookmark_id)
        return _to_response(bookmark)

    async def delete(self, bookmark_id: str) -> None:
        deleted = await self._repo.delete(bookmark_id)
        if not deleted:
            raise BookmarkNotFound(bookmark_id)

    async def exists(self, url: str) -> dict:
        found, bookmark_id = await self._repo.exists(url)
        return {"exists": found, "id": bookmark_id}

    async def list(
        self,
        search: str | None = None,
        tags: str | None = None,
        sort: str | None = None,
        page: int = 1,
        page_size: int = 20,
        favourite: bool | None = None,
    ) -> PaginatedBookmarkResponse:
        tag_names = [t.strip() for t in tags.split(",")] if tags else None
        sort_field = "created_at"
        sort_direction = "desc"
        if sort:
            parts = sort.split(":")
            sort_field = parts[0]
            sort_direction = parts[1] if len(parts) > 1 else "desc"

        bookmarks, total = await self._repo.search(
            query=search,
            tag_names=tag_names,
            sort_field=sort_field,
            sort_direction=sort_direction,
            page=page,
            page_size=page_size,
            favourite=favourite,
        )
        import math

        pages = math.ceil(total / page_size) if page_size else 1
        return PaginatedBookmarkResponse(
            items=[_to_response(b) for b in bookmarks],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
