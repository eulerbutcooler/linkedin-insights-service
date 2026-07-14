from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings=get_settings()
    app.state.mongo=AsyncIOMotorClient(settings.mongo_url)
    app.state.db=app.state.mongo["linkedin_insights"]
    yield
    app.state.mongo.close()


app=FastAPI(lifespan=lifespan)

@app.get("/healthz")
async def healthz():
    return {"status":"ok"}

@app.get("/readyz")
async def readyz():
    try:
        await app.state.db.command("ping")
        return {"status": "ok", "checks":{"mongo": "ok"}}
    except Exception as exc:
        return {"status": "fail", "checks":{"mongo": f"fail:{exc}"}}
