from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.v1.routers import pages, posts, people
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware, register_exception_handlers
from app.db.indexes import ensure_indexes
from app.scrapers.apify_client import ApifyClient

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.mongo = AsyncIOMotorClient(settings.mongo_url)
    app.state.db = app.state.mongo["linkedin_insights"]
    try:
        await app.state.db.command("ping")
        logger.info("mongo.connected", mongo_url=settings.mongo_url)
        await ensure_indexes(app.state.db)
        logger.info("indexes.ready")
    except Exception as exc:
        logger.error("mongo.unreachable", mongo_url=settings.mongo_url, error=str(exc))
    if settings.apify_api_token is None:
        raise RuntimeError("APIFY_API_TOKEN is not configured")
    app.state.apify = ApifyClient(settings.apify_api_token)
    logger.info("apify.ready")
    yield
    logger.info("shutdown.complete")
    app.state.mongo.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)
register_exception_handlers(app)
app.include_router(pages.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(people.router, prefix="/api/v1")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    try:
        await app.state.db.command("ping")
        return {"status": "ok", "checks": {"mongo": "ok"}}
    except Exception as exc:
        return {"status": "fail", "checks": {"mongo": f"fail: {exc}"}}
