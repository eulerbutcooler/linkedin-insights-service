from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.post import CommentDocument, PostDocument
from app.repositories.base import find_keyset


class PostRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db["posts"]

    async def find_by_post_id(self, post_id: str) -> PostDocument | None:
        doc = await self._collection.find_one({"post_id": post_id})
        return PostDocument.model_validate(doc) if doc else None

    async def upsert(self, post: PostDocument) -> PostDocument:
        update_data = post.model_dump()
        update_data.pop("_id", None)
        result = await self._collection.find_one_and_update(
            {"post_id": post.post_id},
            {"$set": update_data},
            upsert=True,
            return_document=True,
        )
        return PostDocument.model_validate(result)

    async def find_recent_for_page(
        self,
        page_id: str,
        cursor: str | None = None,
        size: int = 10,
    ) -> tuple[list[PostDocument], str | None]:
        docs, next_cursor = await find_keyset(
            collection=self._collection,
            filter_doc={"page_id": page_id},
            sort_spec=[("posted_at", -1), ("_id", -1)],
            size=size,
            cursor=cursor,
        )
        return [PostDocument.model_validate(d) for d in docs], next_cursor


class CommentRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db["comments"]
    async def upsert(self, comment: CommentDocument) -> CommentDocument:
        update_data = comment.model_dump()
        update_data.pop("_id", None)
        result = await self._collection.find_one_and_update(
            {"comment_id": comment.comment_id},
            {"$set": update_data},
            upsert=True,
            return_document=True,
        )
        return CommentDocument.model_validate(result)

    async def find_for_post(
        self,
        post_id: str,
        cursor: str | None = None,
        size: int = 20,
    ) -> tuple[list[CommentDocument], str | None]:
        docs, next_cursor = await find_keyset(
            collection=self._collection,
            filter_doc={"post_id": post_id},
            sort_spec=[("posted_at", 1), ("_id", 1)],
            size=size,
            cursor=cursor,
        )
        return [CommentDocument.model_validate(d) for d in docs], next_cursor
