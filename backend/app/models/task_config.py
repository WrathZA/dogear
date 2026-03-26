import uuid

from sqlalchemy import Boolean, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaskConfig(Base):
    __tablename__ = "task_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    task_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    run_on_create: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    run_on_update: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    url_patterns: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    schedule_interval_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
