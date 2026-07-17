# Linkedin Insights Service

A small fastapi based microservice that takes in Linkedin company pageID (deepsolv from https://linkedin.com/company/deepsolv) and shows the company's details, recent posts, comments on those posts and empolyees via a REST API.

The initial scraping of a new company takes time but once its done the fetching is done instantly.

### Stack
I've used Apify for scraping, MongDB for storing the data and Fastapi for building the server.
Docker to containerize the app. Pydantic for schemas and structlog for JSON logs.


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
2. ``` cp .env.example .env```
3. Edit .env and paste the token
4. Run with docker - `docker compose up -build`


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

---

## PROJECT STRUCTURE

```
app/
  main.py                     # FastAPI app, lifespan, router wiring
  core/
    config.py                 # Settings (from env / .env)
    logging.py                # structlog JSON logging
    middleware.py             # request-id middleware + exception handlers
    exceptions.py             # domain error hierarchy
  db/
    indexes.py                # ensure_indexes() — called on startup
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
  api/v1/
    deps.py                   # FastAPI dependency providers
    routers/
      pages.py                # /pages routes
      posts.py                # /posts routes
      people.py               # /people route
main.py                       # entry point
Dockerfile
docker-compose.yml            # api + mongo
.env.example
```
