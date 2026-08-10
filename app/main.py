"""Application entry point.

This module creates the FastAPI application instance. Uvicorn imports
`app` from here to serve it. Route definitions currently live here too;
they'll move to routes.py once there are enough of them to warrant
separating endpoint logic from app configuration.
"""

from fastapi import FastAPI

app = FastAPI(title="Secure Credit Card Tokenization Service")


@app.get("/hello")
def say_hello() -> dict[str, str]:
    """Basic endpoint to verify the server is running."""
    return {"message": "Hello, tokenization service is running!"}
