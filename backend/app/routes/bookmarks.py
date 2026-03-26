from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    PaginatedBookmarkResponse,
)
from app.services.bookmark import BookmarkService, BookmarkNotFound

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


def _service(session: AsyncSession = Depends(get_session)) -> BookmarkService:
    return BookmarkService(session)


@router.get("/exists")
async def bookmark_exists(
    url: str = Query(...),
    svc: BookmarkService = Depends(_service),
) -> dict:
    return await svc.exists(url)


@router.get("", response_model=PaginatedBookmarkResponse)
async def list_bookmarks(
    search: str | None = Query(None),
    tags: str | None = Query(None),
    sort: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    favourite: bool | None = Query(None),
    svc: BookmarkService = Depends(_service),
) -> PaginatedBookmarkResponse:
    return await svc.list(
        search=search,
        tags=tags,
        sort=sort,
        page=page,
        page_size=page_size,
        favourite=favourite,
    )


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: str,
    svc: BookmarkService = Depends(_service),
) -> BookmarkResponse:
    try:
        return await svc.get(bookmark_id)
    except BookmarkNotFound:
        raise HTTPException(status_code=404, detail="Bookmark not found")


@router.post("", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    data: BookmarkCreate,
    svc: BookmarkService = Depends(_service),
) -> BookmarkResponse:
    return await svc.create_or_update(data)


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: str,
    data: BookmarkUpdate,
    svc: BookmarkService = Depends(_service),
) -> BookmarkResponse:
    try:
        return await svc.update(bookmark_id, data)
    except BookmarkNotFound:
        raise HTTPException(status_code=404, detail="Bookmark not found")


@router.delete("/{bookmark_id}", status_code=204)
async def delete_bookmark(
    bookmark_id: str,
    svc: BookmarkService = Depends(_service),
) -> None:
    try:
        await svc.delete(bookmark_id)
    except BookmarkNotFound:
        raise HTTPException(status_code=404, detail="Bookmark not found")
