from datetime import datetime

from pydantic import BaseModel


class BookmarkCreate(BaseModel):
    url: str
    name: str | None = None
    description: str | None = None
    tags: list[str] = []
    favourite: bool = False


class BookmarkUpdate(BaseModel):
    url: str | None = None
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    favourite: bool | None = None
    screenshot_path: str | None = None


class BookmarkResponse(BaseModel):
    id: str
    url: str
    name: str | None
    description: str | None
    screenshot_path: str | None
    favourite: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedBookmarkResponse(BaseModel):
    items: list[BookmarkResponse]
    total: int
    page: int
    page_size: int
    pages: int
