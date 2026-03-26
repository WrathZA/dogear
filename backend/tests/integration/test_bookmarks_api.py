import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app
import app.models  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_bookmark(client):
    response = await client.post("/api/bookmarks", json={"url": "https://example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["id"] is not None
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_create_bookmark_with_all_fields(client):
    response = await client.post(
        "/api/bookmarks",
        json={
            "url": "https://example.com",
            "name": "Example",
            "description": "A site",
            "tags": ["web", "test"],
            "favourite": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Example"
    assert data["favourite"] is True
    assert set(data["tags"]) == {"web", "test"}


@pytest.mark.asyncio
async def test_create_duplicate_url_upserts(client):
    r1 = await client.post(
        "/api/bookmarks", json={"url": "https://example.com", "name": "First"}
    )
    r2 = await client.post(
        "/api/bookmarks", json={"url": "https://example.com", "name": "Second"}
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]
    assert r2.json()["name"] == "Second"


@pytest.mark.asyncio
async def test_get_bookmark(client):
    created = await client.post("/api/bookmarks", json={"url": "https://example.com"})
    bookmark_id = created.json()["id"]

    response = await client.get(f"/api/bookmarks/{bookmark_id}")
    assert response.status_code == 200
    assert response.json()["id"] == bookmark_id


@pytest.mark.asyncio
async def test_get_bookmark_not_found(client):
    response = await client.get("/api/bookmarks/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_bookmark(client):
    created = await client.post(
        "/api/bookmarks", json={"url": "https://example.com", "name": "Old"}
    )
    bookmark_id = created.json()["id"]

    response = await client.put(
        f"/api/bookmarks/{bookmark_id}", json={"name": "New", "favourite": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New"
    assert data["favourite"] is True


@pytest.mark.asyncio
async def test_update_bookmark_not_found(client):
    response = await client.put("/api/bookmarks/nonexistent-id", json={"name": "X"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_bookmark(client):
    created = await client.post("/api/bookmarks", json={"url": "https://example.com"})
    bookmark_id = created.json()["id"]

    delete_response = await client.delete(f"/api/bookmarks/{bookmark_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/bookmarks/{bookmark_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_bookmark_not_found(client):
    response = await client.delete("/api/bookmarks/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_bookmarks_paginated(client):
    for i in range(5):
        await client.post("/api/bookmarks", json={"url": f"https://example{i}.com"})

    response = await client.get("/api/bookmarks?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_list_bookmarks_search(client):
    await client.post(
        "/api/bookmarks", json={"url": "https://python.org", "name": "Python"}
    )
    await client.post(
        "/api/bookmarks", json={"url": "https://rust-lang.org", "name": "Rust"}
    )

    response = await client.get("/api/bookmarks?search=python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["url"] == "https://python.org"


@pytest.mark.asyncio
async def test_list_bookmarks_filter_by_tags(client):
    await client.post(
        "/api/bookmarks", json={"url": "https://a.com", "tags": ["python"]}
    )
    await client.post("/api/bookmarks", json={"url": "https://b.com", "tags": ["rust"]})

    response = await client.get("/api/bookmarks?tags=python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["url"] == "https://a.com"


@pytest.mark.asyncio
async def test_list_bookmarks_filter_by_favourite(client):
    await client.post(
        "/api/bookmarks", json={"url": "https://a.com", "favourite": True}
    )
    await client.post(
        "/api/bookmarks", json={"url": "https://b.com", "favourite": False}
    )

    response = await client.get("/api/bookmarks?favourite=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["url"] == "https://a.com"


@pytest.mark.asyncio
async def test_exists_returns_true(client):
    created = await client.post("/api/bookmarks", json={"url": "https://example.com"})
    bookmark_id = created.json()["id"]

    response = await client.get("/api/bookmarks/exists?url=https://example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["id"] == bookmark_id


@pytest.mark.asyncio
async def test_exists_returns_false(client):
    response = await client.get("/api/bookmarks/exists?url=https://nothere.com")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
    assert data["id"] is None


@pytest.mark.asyncio
async def test_create_bookmark_missing_url(client):
    response = await client.post("/api/bookmarks", json={"name": "No URL"})
    assert response.status_code == 422
