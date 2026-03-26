import pytest

from app.repositories.bookmark import BookmarkRepository


@pytest.mark.asyncio
async def test_upsert_creates_bookmark(db_session):
    repo = BookmarkRepository(db_session)
    bookmark = await repo.upsert(
        url="https://example.com",
        name="Example",
        description="A test bookmark",
        tags=["python", "test"],
        favourite=False,
    )
    assert bookmark.id is not None
    assert bookmark.url == "https://example.com"
    assert bookmark.name == "Example"
    assert {t.name for t in bookmark.tags} == {"python", "test"}


@pytest.mark.asyncio
async def test_upsert_overwrites_on_duplicate_url(db_session):
    repo = BookmarkRepository(db_session)
    first = await repo.upsert(
        url="https://example.com",
        name="Original",
        description=None,
        tags=["old"],
        favourite=False,
    )
    second = await repo.upsert(
        url="https://example.com",
        name="Updated",
        description="Now has description",
        tags=["new"],
        favourite=True,
    )
    assert first.id == second.id
    assert second.name == "Updated"
    assert second.favourite is True
    assert {t.name for t in second.tags} == {"new"}


@pytest.mark.asyncio
async def test_search_by_keyword_in_name(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://python.org",
        name="Python Docs",
        description=None,
        tags=[],
        favourite=False,
    )
    await repo.upsert(
        url="https://rust-lang.org",
        name="Rust Lang",
        description=None,
        tags=[],
        favourite=False,
    )

    results, total = await repo.search(query="python")
    assert total == 1
    assert results[0].url == "https://python.org"


@pytest.mark.asyncio
async def test_search_by_keyword_in_url(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://docs.python.org",
        name=None,
        description=None,
        tags=[],
        favourite=False,
    )
    await repo.upsert(
        url="https://rust-lang.org",
        name=None,
        description=None,
        tags=[],
        favourite=False,
    )

    results, total = await repo.search(query="python")
    assert total == 1


@pytest.mark.asyncio
async def test_search_by_keyword_in_description(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://a.com",
        name="A",
        description="has python content",
        tags=[],
        favourite=False,
    )
    await repo.upsert(
        url="https://b.com",
        name="B",
        description="has rust content",
        tags=[],
        favourite=False,
    )

    results, total = await repo.search(query="python")
    assert total == 1


@pytest.mark.asyncio
async def test_search_by_keyword_in_tags(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://a.com",
        name="A",
        description=None,
        tags=["python", "dev"],
        favourite=False,
    )
    await repo.upsert(
        url="https://b.com", name="B", description=None, tags=["rust"], favourite=False
    )

    results, total = await repo.search(query="python")
    assert total == 1
    assert results[0].url == "https://a.com"


@pytest.mark.asyncio
async def test_filter_by_single_tag(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://a.com",
        name="A",
        description=None,
        tags=["python"],
        favourite=False,
    )
    await repo.upsert(
        url="https://b.com", name="B", description=None, tags=["rust"], favourite=False
    )
    await repo.upsert(
        url="https://c.com",
        name="C",
        description=None,
        tags=["python", "web"],
        favourite=False,
    )

    results, total = await repo.search(tag_names=["python"])
    assert total == 2
    urls = {r.url for r in results}
    assert urls == {"https://a.com", "https://c.com"}


@pytest.mark.asyncio
async def test_filter_by_multiple_tags_requires_all(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://a.com",
        name="A",
        description=None,
        tags=["python", "web"],
        favourite=False,
    )
    await repo.upsert(
        url="https://b.com",
        name="B",
        description=None,
        tags=["python"],
        favourite=False,
    )

    results, total = await repo.search(tag_names=["python", "web"])
    assert total == 1
    assert results[0].url == "https://a.com"


@pytest.mark.asyncio
async def test_filter_by_favourite(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://a.com", name="A", description=None, tags=[], favourite=True
    )
    await repo.upsert(
        url="https://b.com", name="B", description=None, tags=[], favourite=False
    )

    results, total = await repo.search(favourite=True)
    assert total == 1
    assert results[0].url == "https://a.com"


@pytest.mark.asyncio
async def test_sort_by_name_asc(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://z.com", name="Zebra", description=None, tags=[], favourite=False
    )
    await repo.upsert(
        url="https://a.com", name="Apple", description=None, tags=[], favourite=False
    )
    await repo.upsert(
        url="https://m.com", name="Mango", description=None, tags=[], favourite=False
    )

    results, _ = await repo.search(sort_field="name", sort_direction="asc")
    assert [r.name for r in results] == ["Apple", "Mango", "Zebra"]


@pytest.mark.asyncio
async def test_sort_by_name_desc(db_session):
    repo = BookmarkRepository(db_session)
    await repo.upsert(
        url="https://z.com", name="Zebra", description=None, tags=[], favourite=False
    )
    await repo.upsert(
        url="https://a.com", name="Apple", description=None, tags=[], favourite=False
    )

    results, _ = await repo.search(sort_field="name", sort_direction="desc")
    assert results[0].name == "Zebra"


@pytest.mark.asyncio
async def test_paginate_returns_correct_page(db_session):
    repo = BookmarkRepository(db_session)
    for i in range(5):
        await repo.upsert(
            url=f"https://example{i}.com",
            name=f"Bookmark {i}",
            description=None,
            tags=[],
            favourite=False,
        )

    results, total = await repo.search(page=1, page_size=2)
    assert total == 5
    assert len(results) == 2

    results_p2, _ = await repo.search(page=2, page_size=2)
    assert len(results_p2) == 2

    results_p3, _ = await repo.search(page=3, page_size=2)
    assert len(results_p3) == 1


@pytest.mark.asyncio
async def test_exists_returns_true_with_id(db_session):
    repo = BookmarkRepository(db_session)
    bookmark = await repo.upsert(
        url="https://example.com", name=None, description=None, tags=[], favourite=False
    )
    found, bookmark_id = await repo.exists("https://example.com")
    assert found is True
    assert bookmark_id == bookmark.id


@pytest.mark.asyncio
async def test_exists_returns_false_for_unknown(db_session):
    repo = BookmarkRepository(db_session)
    found, bookmark_id = await repo.exists("https://nothere.com")
    assert found is False
    assert bookmark_id is None


@pytest.mark.asyncio
async def test_delete_removes_bookmark(db_session):
    repo = BookmarkRepository(db_session)
    bookmark = await repo.upsert(
        url="https://example.com", name=None, description=None, tags=[], favourite=False
    )
    deleted = await repo.delete(bookmark.id)
    assert deleted is True
    assert await repo.get_by_id(bookmark.id) is None


@pytest.mark.asyncio
async def test_delete_returns_false_for_missing(db_session):
    repo = BookmarkRepository(db_session)
    deleted = await repo.delete("nonexistent-id")
    assert deleted is False
