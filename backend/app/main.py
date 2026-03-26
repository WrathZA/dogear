from fastapi import FastAPI

app = FastAPI(title="bookmark-it")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
