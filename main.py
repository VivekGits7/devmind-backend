from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from logger import setup_logging, get_logger
from services.database import create_db_pool, close_db_pool
from routers.auth import router as auth_router
from limiter import limiter
from error import setup_error_handlers
from middleware.request_logging import RequestLoggingMiddleware, SecurityHeadersMiddleware

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    await create_db_pool()
    logger.info("Database pool created")

    yield

    # Shutdown
    await close_db_pool()
    logger.info("Database pool closed")


# Create FastAPI application
app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description=f"{settings.APP_NAME} Backend API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
)

# Rate limiter setup
app.state.limiter = limiter

# Setup universal error handlers
setup_error_handlers(app)

# Rate limit exceeded handler (after error handlers)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware (LIFO order — last added, first executed)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS Configuration
if settings.ENVIRONMENT != "production":
    logger.info("CORS is enabled for development environment.")
    allowed_origins = ["*"]
else:
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if allowed_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)


# ==================== HEALTH ENDPOINTS ====================


@app.get("/", tags=["Health"])
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": f"{settings.APP_NAME}-api"}


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT != "production",
    )
