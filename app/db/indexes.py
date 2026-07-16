from motor.motor_asyncio import AsyncIOMotorDatabase

async def ensure_indexes(db: AsyncIOMotorDatabase)->None:
    pages=db["pages"]

    await pages.create_index(
        "linkedin_id",
        unique=True,
        name="linkedin_id_unique",
    )

    await pages.create_index(
        [("name", "text")],
        name="name_text"
    )

    await pages.create_index(
        [("industry", 1), ("total_followers",1)],
        name="industry_followers"
    )

    await pages.create_index(
        [("updated_at",-1)],
        name="updated_at_desc"
    )
