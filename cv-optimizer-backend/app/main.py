import json
import warnings
import re
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.api import api_router

# Suppress pypdf/cryptography deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pypdf")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="cryptography")

# Initialize logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

@app.middleware("http")
async def sanitize_json_middleware(request: Request, call_next):
    """
    Middleware to catch and fix invalid control characters in JSON bodies
    before they reach the FastAPI parser.
    
    Skips streaming endpoints to avoid interfering with SSE.
    """
    # Skip middleware for streaming endpoints
    if "/stream" in request.url.path:
        response = await call_next(request)
        return response
    
    if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("Content-Type", ""):
        body = await request.body()
        if body:
            try:
                # Decode body
                decoded_body = body.decode("utf-8")
                
                # Helper function to escape control characters in matched strings
                def escape_inside_quotes(match):
                    content = match.group(0)
                    # Escape raw newlines, carriage returns, and tabs
                    content = content.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                    # Escape other non-printable characters
                    return "".join(
                        char if ord(char) >= 32 or char == '"' or char == '\\' 
                        else f"\\u{ord(char):04x}" 
                        for char in content
                    )

                # Regex to find JSON strings: " followed by anything not a " (handling escaped quotes)
                sanitized_body = re.sub(r'"(?:\\.|[^"\\])*"', escape_inside_quotes, decoded_body)
                
                # Update the request body
                async def receive():
                    return {"type": "http.request", "body": sanitized_body.encode("utf-8")}
                
                request._receive = receive
            except Exception:
                # If decoding fails, let it pass to standard error handling
                pass
                
    response = await call_next(request)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("validation_error", errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact support."},
    )

# Set up CORS
# allow_credentials=True is required for HttpOnly cookies to be sent cross-origin.
# In production replace the origins list with your actual frontend domain.
ALLOWED_ORIGINS = (
    ["https://your-production-domain.com"]
    if settings.is_production
    else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,   # MUST be True for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    logger.info("health_check_triggered")
    return {"status": "healthy", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
