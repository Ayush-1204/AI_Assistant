from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():

    return {
        "name": "Second Brain API",
        "version": "0.1.0",
        "status": "healthy",
    }


@router.get("/health")
async def health():

    return {
        "status": "healthy",
    }