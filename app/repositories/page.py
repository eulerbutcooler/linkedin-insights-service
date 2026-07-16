from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import find_keyset
from app.db.page import PageDocument

class PageRepository:

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection=db["pages"]

    async def find_by_linkedin_id(self,linkedin_id:str)->PageDocument | None:
        doc=await self._collection.find_one({"linkedin_id":linkedin_id})
        if doc is None:
            return None
        return PageDocument.model_validate(doc)

    async def upsert(self,page:PageDocument)-> PageDocument:
        update_data=page.model_dump()
        from datetime import datetime, timezone
        update_data["updated_at"]=datetime.now(timezone.utc)

        update_data.pop("_id",None)

        result=await self._collection.find_one_and_update(
            {"linkedin_id":page.linkedin_id},
            {"$set":update_data},
            upsert=True,
            return_document=True
        )
        return PageDocument.model_validate(result)

    async def find_many(
        self, filter_doc: dict[str,Any],cursor: str |None = None,size:int=20
    )->tuple[list[PageDocument], str | None]:
        docs,next_cursor=await find_keyset(
            collection=self._collection,
            filter_doc=filter_doc,
            sort_spec=[("_id", -1)],
            size=size,
            cursor=cursor
        )
        pages=[PageDocument.model_validate(doc) for doc in docs]
        return pages, next_cursor
