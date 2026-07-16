import base64
import json
from typing import Any, Sequence

from motor.motor_asyncio import AsyncIOMotorCollection


def encode_cursor(state: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(state, default=str).encode()).decode()


def decode_cursor(cursor: str | None) -> dict[str, Any] | None:
    if not cursor:
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        return None


def _cursor_predicate(
    state: dict[str, Any],
    sort_spec: Sequence[tuple[str, int]],
) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = []
    for i in range(len(sort_spec)):
        equal_part: dict[str, Any] = {}
        for field, _ in sort_spec[:i]:
            equal_part[field] = state[field]
        field, direction = sort_spec[i]
        op = "$lt" if direction == -1 else "$gt"
        equal_part[field] = {op: state[field]}
        clauses.append(equal_part)
    return {"$or": clauses}


async def find_keyset(
    collection: AsyncIOMotorCollection,
    filter_doc: dict[str, Any],
    sort_spec: Sequence[tuple[str, int]],
    size: int,
    cursor: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    query = dict(filter_doc)
    state = decode_cursor(cursor)

    if state:
        predicate = _cursor_predicate(state, sort_spec)
        query = {"$and": [filter_doc, predicate]} if filter_doc else predicate

    docs = await collection.find(query).sort(sort_spec).limit(size + 1).to_list(size + 1)
    has_more = len(docs) > size
    docs = docs[:size]

    next_cursor = None
    if has_more and docs:
        last = docs[-1]
        next_state = {field: last[field] for field, _ in sort_spec if field in last}
        next_cursor = encode_cursor(next_state)

    return docs, next_cursor
