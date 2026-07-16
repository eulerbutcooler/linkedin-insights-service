class DomainError(Exception):
    code = "INTERNAL"
    status = 500

class NotFoundError(DomainError):
    code = "NOT_FOUND"
    status = 404

class ScrapeError(DomainError):
    code = "SCRAPE_FAILED"
    status = 424

class ValidationError(DomainError):
    code = "VALIDATION"
    status = 422
