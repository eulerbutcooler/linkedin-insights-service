# Linkedin Insights Service

A small fastapi based microservice that takes in Linkedin company pageID (deepsolv from https://linkedin.com/company/deepsolv) and shows the company's details, recent posts, comments on those posts and empolyees via a REST API.

The initial scraping of a new company takes time but once its done the fetching is done instantly.

### Stack
I've used Apify for scraping, MongoDB for storage, Redis for caching, Gemini for AI summaries and FastAPI for the server.


Given a company pageID, the service will return:
```
"linkedin_id":
   "url":
   "name":
   "tagline":
   "industry":
   "total_followers":
   "logo_url": 
   "description":
   "website":
   "headquarters":
   "company_size": 
   "scraped_at": 
   "updated_at":
```

## Setup

1. Get Apify token
2. Get Gemini API key 
3. ``` cp .env.example .env```
4. Edit .env and paste the token
5. Run with docker - `docker compose up --build`


## Endpoints

BaseURL - http://localhost:8000 \
Interactive Swagger docs - http://localhost:8000/docs \
OpenAPI spec - http://localhost:8000/openapi.json (This can be imported in Postman) 

### HEALTH

1. GET - `/healthz` - Checks if Backend is up
2. GET - `/readyz` - Checks if DB is up

## PAGES (Companies)

1. GET - `/api/v1/pages` - Lists all scrapped companies
2. GET - `/api/v1/pages/{linkedin_id}` - Returns the company from DB if present, otherwise scrapes it via Apify, stores, and returns.
3. POST - `/api/v1/pages/{linkedin_id}/refresh` - Forces a fresh scrape (bypasses the db cache)

## SUMMARY

1. GET - `api/v1/pages/{linkedin_id}/summary` - Generates a business summary of the company using Gemini based on stored PageDocument + recent posts. Cached by content hash so it is recomputed only when the underlying data changes.

(Requires `GEMINI_API_KEY` to be set.)

Response:

```
{
  "linkedin_id": "keploy",
  "summary": "**Company Summary: Keploy** ...",
  "content_hash": "00c10dee...",
  "cached": false
}
```

**Filters for GET /api/v1/pages**

1. `name` | string | `?name=deepsolv` | Text search on company name
2. `industry` | string | `?industry=software%20development` | Exact match on industry
3. `followers_min` | int | `?followers_min=1000` | Inclusive lower bound
4. `followers_max` | int | `?followers_max=50000` | Inclusive upper bound
5. `size` | int | `?size=10` | Page size (1-50, default 20)
6. `cursor` | string | `?cursor=eyJ...` | Opaque cursor from a previous response's `next_cursor`

## POSTS 

1. GET - `/api/v1/pages/{linkedin_id}/posts` - Recent posts for a company. Newest first and paginated.
2. GET - `/api/v1/pages/{linkedin_id}/posts/{post_id}` - A single post plus its first 20 comments.
3. GET - `/api/v1/pages/{linkedin_id}/posts/{post_id}/comments` - Paginated comments for a single post.

## PEOPLE

1. GET - `/api/v1/pages/{linkedin_id}/people` - Employees of the company.

---

## NOTES

1. Every endpoint returns:
```
{
  "items": [...],
  "next_cursor": "eyJ... or null"
}
```
Pass `next_cursor` as the `cursor` query param on the next call to fetch
the next page. When `next_cursor` is `null`, no more items exist.


2. The `request_id` is also returned in the `x-request-id` response header \
and threaded through every log line for that request, so you can grep \
    the logs by a single ID to see the full request trail.

```{
  "error": {
    "code": "NOT_FOUND",
    "message": "Post abc not found for page keploy",
    "request_id": "8a51f46b-..."
  }
}
```

3. Import `postman/Postman_collection.json` in Postman. \
Set baseurl = http://localhost:8000

4. Caching
  - GET `pages/{id}` - Cached in Redis for 5 minutes. The first call scrapes while the \ subsequent ones are returned instantly from cache.
  - POST `/pages/{id}/refresh` - Invalidates the caches and re-scrapes.
  - `/pages/{id}/summary` - Cached by content hash and is only recomputed when the company's data \ or recent posts actually change.
  - If Redis is down, the API always hits the DB. 

---

## PROJECT STRUCTURE

```
app/
  main.py                     # FastAPI app, lifespan, router wiring
  cache.py                    # Redis cache 
  llm.py                      # Gemini LLM client
  core/
    config.py                 # Settings (from env / .env)
    logging.py                # structlog JSON logging
    middleware.py             # request-id middleware + exception handlers
    exceptions.py             # domain error hierarchy
  db/
    indexes.py                # ensure_indexes() - called on startup
    page.py                   # PageDocument schema + raw→document mapper
    post.py                   # PostDocument + CommentDocument + mappers
    person.py                 # PersonDocument + mapper
  repositories/
    base.py                   # shared keyset pagination helper
    page.py                   # PageRepository
    post.py                   # PostRepository, CommentRepository, PersonRepository
  scrapers/
    dto.py                    # RawPage, RawPost, RawComment, RawPerson
    apify_client.py           # ApifyClient, wraps three Apify actors
  services/
    page_service.py           # get_or_fetch orchestration
    summary_service.py        # AI summary with content-hash caching
  api/v1/
    deps.py                   # FastAPI dependency providers
    routers/
      pages.py                # /pages routes
      posts.py                # /posts routes
      people.py               # /people route
      summary.py              # /summary route
main.py                       # entry point
Dockerfile
docker-compose.yml            # api + mongo + redis
.env.example

```

## HOW TO TEST EVERY ENDPOINT

1. Health
`curl http://localhost:8000/healthz` \
`curl http://localhost:8000/readyz`

2. Get a company
`curl http://localhost:8000/api/v1/pages/deepsolv`

3. List scraped companies
`curl http://localhost:8000/api/v1/pages`

4. Filter companies
`curl http://localhost:8000/api/v1/pages?industry=software&followers_min=1000`

5. Search by name
`curl http://localhost:8000/api/v1/pages?name=deepsolv`

6. Paginate (take next_cursor from 3's response)
`curl http://localhost:8000/api/v1/pages?size=2&cursor=PASTE_CURSOR_HERE`

7. Force a fresh scrape
`curl -X POST http://localhost:8000/api/v1/pages/deepsolv/refresh`

8. Recent posts
`curl http://localhost:8000/api/v1/pages/deepsolv/posts`

9. Single post + first 20 comments
`curl http://localhost:8000/api/v1/pages/deepsolv/posts/PASTE_POST_ID`

10. Paginated comments for one post
`curl http://localhost:8000/api/v1/pages/deepsolv/posts/PASTE_POST_ID/comments`

11. Employees
`curl http://localhost:8000/api/v1/pages/deepsolv/people`

12. AI summary
`curl http://localhost:8000/api/v1/pages/deepsolv/summary`
