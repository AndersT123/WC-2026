from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_root():
    """Root endpoint returning welcome message."""
    return {"message": "Hello World"}


@router.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
