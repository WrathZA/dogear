import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark, bookmark_tags
from app.models.tag import Tag


class BookmarkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        url: str,
        name: str | None,
        description: str | None,
        tags: list[str],
        favourite: bool,
        screenshot_path: str | None = None,
    ) -> Bookmark:
        result = await self._session.execute(
            select(Bookmark).where(Bookmark.url == url)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.name = name if name is not None else existing.name
            existing.description = (
                description if description is not None else existing.description
            )
            existing.favourite = favourite
            existing.updated_at = datetime.utcnow()
            if screenshot_path is not None:
                existing.screenshot_path = screenshot_path
            bookmark = existing
        else:
            bookmark = Bookmark(
                id=str(uuid.uuid4()),
                url=url,
                name=name,
                description=description,
                favourite=favourite,
                screenshot_path=screenshot_path,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self._session.add(bookmark)

        await self._session.flush()
        await self._sync_tags(bookmark, tags)
        await self._session.commit()
        await self._session.refresh(bookmark)
        return bookmark

    async def get_by_id(self, bookmark_id: str) -> Bookmark | None:
        result = await self._session.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id)
        )
        return result.scalar_one_or_none()

    async def update(self, bookmark_id: str, **fields) -> Bookmark | None:
        bookmark = await self.get_by_id(bookmark_id)
        if bookmark is None:
            return None

        tags = fields.pop("tags", None)
        for key, value in fields.items():
            if value is not None:
                setattr(bookmark, key, value)
        bookmark.updated_at = datetime.utcnow()

        await self._session.flush()
        if tags is not None:
            await self._sync_tags(bookmark, tags)
        await self._session.commit()
        await self._session.refresh(bookmark)
        return bookmark

    async def delete(self, bookmark_id: str) -> bool:
        bookmark = await self.get_by_id(bookmark_id)
        if bookmark is None:
            return False
        await self._session.delete(bookmark)
        await self._session.commit()
        return True

    async def exists(self, url: str) -> tuple[bool, str | None]:
        result = await self._session.execute(
            select(Bookmark.id).where(Bookmark.url == url)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False, None
        return True, row

    async def search(
        self,
        query: str | None = None,
        tag_names: list[str] | None = None,
        sort_field: str = "created_at",
        sort_direction: str = "desc",
        page: int = 1,
        page_size: int = 20,
        favourite: bool | None = None,
    ) -> tuple[list[Bookmark], int]:
        stmt = select(Bookmark)

        if query:
            tag_subq = (
                select(bookmark_tags.c.bookmark_id)
                .join(Tag, Tag.id == bookmark_tags.c.tag_id)
                .where(Tag.name.ilike(f"%{query}%"))
            )
            stmt = stmt.where(
                or_(
                    Bookmark.url.ilike(f"%{query}%"),
                    Bookmark.name.ilike(f"%{query}%"),
                    Bookmark.description.ilike(f"%{query}%"),
                    Bookmark.id.in_(tag_subq),
                )
            )

        if tag_names:
            for tag_name in tag_names:
                tag_subq = (
                    select(bookmark_tags.c.bookmark_id)
                    .join(Tag, Tag.id == bookmark_tags.c.tag_id)
                    .where(Tag.name == tag_name)
                )
                stmt = stmt.where(Bookmark.id.in_(tag_subq))

        if favourite is not None:
            stmt = stmt.where(Bookmark.favourite == favourite)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        valid_fields = {"created_at", "updated_at", "name", "url"}
        if sort_field not in valid_fields:
            sort_field = "created_at"

        col = getattr(Bookmark, sort_field)
        if sort_direction == "asc":
            stmt = stmt.order_by(col.asc())
        else:
            stmt = stmt.order_by(col.desc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self._session.execute(stmt)
        bookmarks = list(result.scalars().all())
        return bookmarks, total

    async def _sync_tags(self, bookmark: Bookmark, tag_names: list[str]) -> None:
        existing_tags = {t.name: t for t in bookmark.tags}
        desired = set(tag_names)
        current = set(existing_tags)

        # Remove tags no longer needed
        for name in current - desired:
            bookmark.tags.remove(existing_tags[name])

        # Add new tags
        for name in desired - current:
            result = await self._session.execute(select(Tag).where(Tag.name == name))
            tag = result.scalar_one_or_none()
            if tag is None:
                tag = Tag(id=str(uuid.uuid4()), name=name)
                self._session.add(tag)
                await self._session.flush()
            bookmark.tags.append(tag)
