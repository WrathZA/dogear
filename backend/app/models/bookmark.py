import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

bookmark_tags = Table(
    "bookmark_tags",
    Base.metadata,
    Column(
        "bookmark_id",
        String(36),
        ForeignKey("bookmarks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        String(36),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String, nullable=True)
    favourite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary=bookmark_tags, back_populates="bookmarks", lazy="selectin"
    )
