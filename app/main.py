"""Application entry point.

Creates the FastAPI application, registers the API routes, and
installs a custom validation error handler. Uvicorn imports `app`
from here to serve it.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes import router

app = FastAPI(title="Secure Credit Card Tokenization Service")
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return validation errors without echoing back the raw input.

    FastAPI's default handler includes the submitted value in each
    error entry, which would reflect invalid-but-still-sensitive data
    (e.g. a mistyped card number) straight back into the HTTP response
    -- and into anything that logs or monitors it.
    """
    safe_errors = [
        {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": safe_errors})
