from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_comment_repo, get_post_repo
from app.core.exceptions import NotFoundError
from app.repositories.post import CommentRepository, PostRepository

router = APIRouter(tags=["posts"])


@router.get("/pages/{linkedin_id}/posts")
async def list_posts(
    linkedin_id: str,
    cursor: str | None = None,
    size: int = Query(10, ge=1, le=50),
    post_repo: PostRepository = Depends(get_post_repo),
):
    posts, next_cursor = await post_repo.find_recent_for_page(
        linkedin_id, cursor=cursor, size=size
    )
    return {
        "items": [p.model_dump(mode="json") for p in posts],
        "next_cursor": next_cursor,
    }


@router.get("/pages/{linkedin_id}/posts/{post_id}")
async def get_post(
    linkedin_id: str,
    post_id: str,
    post_repo: PostRepository = Depends(get_post_repo),
    comment_repo: CommentRepository = Depends(get_comment_repo),
):
    post = await post_repo.find_by_post_id(post_id)
    if post is None or post.page_id != linkedin_id:
        raise NotFoundError(f"Post {post_id} not found for page {linkedin_id}")
    comments, _ = await comment_repo.find_for_post(post_id, size=20)
    return {
        "post": post.model_dump(mode="json"),
        "comments": [c.model_dump(mode="json") for c in comments],
    }


@router.get("/pages/{linkedin_id}/posts/{post_id}/comments")
async def list_comments(
    linkedin_id: str,
    post_id: str,
    cursor: str | None = None,
    size: int = Query(20, ge=1, le=50),
    comment_repo: CommentRepository = Depends(get_comment_repo),
):
    comments, next_cursor = await comment_repo.find_for_post(
        post_id, cursor=cursor, size=size
    )
    return {
        "items": [c.model_dump(mode="json") for c in comments],
        "next_cursor": next_cursor,
    }
