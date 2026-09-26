import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from core.config import settings
from core.database import Base, engine
from core.exceptions import BaseAPIException

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENV == "development" else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Import routers
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.tasks import router as tasks_router
from routers.chat import router as chat_router
from routers.search import router as search_router
from routers.analytics import router as analytics_router
from routers.calendar import router as calendar_router
from routers.memory import router as memory_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Database Setup
    logger.info("Initializing database extension and tables...")
    try:
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("pgvector extension loaded/verified.")
            except Exception as e:
                logger.warning(f"Could not load pgvector extension: {e}. Semantic search features might degrade.")
                
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables verified.")
    except Exception as e:
        logger.error(f"Database initialization error (skipped for serverless cold start): {e}")
        
    yield
    # Shutdown logic
    logger.info("Shutting down scheduling backend...")
    try:
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade AI Assistant Backend for Scheduling",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(tasks_router, prefix=api_prefix)
app.include_router(chat_router, prefix=api_prefix)
app.include_router(search_router, prefix=api_prefix)
app.include_router(analytics_router, prefix=api_prefix)
app.include_router(calendar_router, prefix=api_prefix)
app.include_router(memory_router, prefix=api_prefix)


# Global custom exception handler
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    if isinstance(exc, (OperationalError, TimeoutError, OSError)):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Database is unavailable. Check database networking, firewall, SSL, and connection string settings.",
                "success": False,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred", "success": False}
    )


@app.get("/")
async def root():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "docs": "/docs"
    }


@app.get("/health/db")
async def database_health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "unreachable",
                "detail": "Could not connect to the configured database.",
            },
        )

    return {"status": "healthy", "database": "reachable"}
