from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware

configure_logging()
logger=get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings=get_settings()
    app.state.mongo=AsyncIOMotorClient(settings.mongo_url)
    app.state.db=app.state.mongo["linkedin_insights"]
    try:
           await app.state.db.command("ping")
           logger.info("mongo.connected", mongo_url=settings.mongo_url)
    except Exception as exc:
           logger.error("mongo.unreachable", mongo_url=settings.mongo_url, error=str(exc))

    yield
    logger.info("shutdown.complete")
    app.state.mongo.close()


app=FastAPI(lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)

@app.get("/healthz")
async def healthz():
    return {"status":"ok"}

@app.get("/readyz")
async def readyz():
    try:
        await app.state.db.command("ping")
        return {"status": "ok", "checks":{"mongo": "ok"}}
    except Exception as exc:
        logger.warning("readyz.mongo_fail", error=str(exc))
        return {"status": "fail", "checks":{"mongo": f"fail:{exc}"}}
