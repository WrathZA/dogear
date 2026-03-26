import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.bookmark import bookmark_tags


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    bookmarks: Mapped[list["Bookmark"]] = relationship(  # noqa: F821
        "Bookmark", secondary=bookmark_tags, back_populates="tags", lazy="selectin"
    )
