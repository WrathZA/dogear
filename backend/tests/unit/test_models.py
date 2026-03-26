import pytest
from sqlalchemy import text

from app.models import Bookmark, Tag, TaskConfig, bookmark_tags


def test_models_importable():
    assert Bookmark.__tablename__ == "bookmarks"
    assert Tag.__tablename__ == "tags"
    assert TaskConfig.__tablename__ == "task_configs"
    assert bookmark_tags.name == "bookmark_tags"


@pytest.mark.asyncio
async def test_schema_creates_all_tables(db_session):
    result = await db_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    )
    tables = {row[0] for row in result.fetchall()}
    assert {"bookmarks", "tags", "task_configs", "bookmark_tags"}.issubset(tables)


@pytest.mark.asyncio
async def test_bookmark_columns(db_session):
    result = await db_session.execute(text("PRAGMA table_info(bookmarks)"))
    columns = {row[1] for row in result.fetchall()}
    assert columns == {
        "id",
        "url",
        "name",
        "description",
        "screenshot_path",
        "favourite",
        "created_at",
        "updated_at",
    }


@pytest.mark.asyncio
async def test_tag_columns(db_session):
    result = await db_session.execute(text("PRAGMA table_info(tags)"))
    columns = {row[1] for row in result.fetchall()}
    assert columns == {"id", "name"}


@pytest.mark.asyncio
async def test_task_config_columns(db_session):
    result = await db_session.execute(text("PRAGMA table_info(task_configs)"))
    columns = {row[1] for row in result.fetchall()}
    assert columns == {
        "id",
        "task_name",
        "enabled",
        "run_on_create",
        "run_on_update",
        "url_patterns",
        "tags",
        "schedule_interval_seconds",
    }


@pytest.mark.asyncio
async def test_bookmark_tags_join_table(db_session):
    result = await db_session.execute(text("PRAGMA table_info(bookmark_tags)"))
    columns = {row[1] for row in result.fetchall()}
    assert columns == {"bookmark_id", "tag_id"}
