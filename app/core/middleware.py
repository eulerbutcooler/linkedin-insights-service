import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from structlog import contextvars as structlog_contextvars


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id=request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id=request_id

        structlog_contextvars.clear_contextvars()
        structlog_contextvars.bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
        finally:
            structlog_contextvars.clear_contextvars()

        response.headers["x-request-id"]=request_id
        return response
