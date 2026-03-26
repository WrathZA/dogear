from fastapi import FastAPI

from app.routes import bookmarks_router

app = FastAPI(title="bookmark-it")

app.include_router(bookmarks_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
