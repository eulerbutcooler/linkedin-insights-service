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

    posts = db["posts"]
    await posts.create_index(
        "post_id",
        unique=True,
        name="post_id_unique",
    )
    await posts.create_index(
        [("page_id", 1), ("posted_at", -1), ("_id", 1)],
        name="page_id_posted_at",
    )

    comments = db["comments"]
    await comments.create_index(
        "comment_id",
        unique=True,
        name="comment_id_unique",
    )
    await comments.create_index(
        [("post_id", 1), ("posted_at", 1)],
        name="post_id_posted_at",
    )
    await comments.create_index(
        [("page_id", 1), ("posted_at", -1)],
        name="page_id_posted_at_desc",
    )

    people = db["people"]
    await people.create_index(
        "person_id",
        unique=True,
        name="person_id_unique",
    )
    await people.create_index(
        [("page_id", 1), ("_id", -1)],
        name="page_id_people",
    )
