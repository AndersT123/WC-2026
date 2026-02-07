import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import auth, health, leagues, matches, predictions, bets, dev
from app.database import init_db, async_session_maker
from app.services.token_service import cleanup_expired_tokens

# Import models to register them with Base.metadata
# This must happen before init_db is called
from app.models.user import User, MagicLinkToken  # noqa: F401
from app.models.league import League, LeagueMembership  # noqa: F401
from app.models.match import Match  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
from app.models.bet import Bet  # noqa: F401


# Background task for cleaning up expired tokens
async def cleanup_tokens_task():
    """Background task that runs periodically to clean up expired tokens."""
    while True:
        try:
            async with async_session_maker() as db:
                deleted_count = await cleanup_expired_tokens(db)
                if deleted_count > 0:
                    print(f"Cleaned up {deleted_count} expired tokens")
        except Exception as e:
            print(f"Error in token cleanup task: {str(e)}")

        # Run every hour
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("Starting up application...")

    # Initialize database tables
    await init_db()

    # Start background task for token cleanup
    cleanup_task = asyncio.create_task(cleanup_tokens_task())

    yield

    # Shutdown
    print("Shutting down application...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="World Cup Predictions API",
    description="API for World Cup prediction game with magic link authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(leagues.router)
app.include_router(matches.router)
app.include_router(predictions.router)
app.include_router(bets.router)
app.include_router(dev.router)  # Dev endpoints (localhost only)

# Serve static files (HTML pages) - must be after all API routes
from fastapi.responses import FileResponse

@app.get("/")
async def serve_root():
    """Serve login.html at root."""
    return FileResponse(Path(__file__).parent.parent / "login.html")

@app.get("/{filename}.html")
async def serve_html(filename: str):
    """Serve HTML files from project root."""
    file_path = Path(__file__).parent.parent / f"{filename}.html"

    # Security: prevent directory traversal
    if ".." in filename:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Not Found")

    return FileResponse(file_path)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    print(f"Unexpected error: {str(exc)}")
    return {
        "detail": "An unexpected error occurred. Please try again later."
    }
