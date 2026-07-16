from fastapi import Depends, Request

from app.core.config import Settings
from app.repositories.page import PageRepository
from app.repositories.post import CommentRepository, PostRepository, PersonRepository
from app.scrapers.apify_client import ApifyClient
from app.services.page_service import PageService


def get_db(request: Request):
    return request.app.state.db

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

def get_apify_client(request: Request) -> ApifyClient:
    return request.app.state.apify

def get_page_repo(db=Depends(get_db)) -> PageRepository:
    return PageRepository(db)

def get_post_repo(db=Depends(get_db)) -> PostRepository:
    return PostRepository(db)

def get_comment_repo(db=Depends(get_db)) -> CommentRepository:
    return CommentRepository(db)

def get_person_repo(db=Depends(get_db)) -> PersonRepository:
    return PersonRepository(db)


def get_page_service(
    page_repo=Depends(get_page_repo),
    post_repo=Depends(get_post_repo),
    comment_repo=Depends(get_comment_repo),
    person_repo=Depends(get_person_repo),
    apify=Depends(get_apify_client),
) -> PageService:
    return PageService(page_repo, post_repo, comment_repo, person_repo, apify)
