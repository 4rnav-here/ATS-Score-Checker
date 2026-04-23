from fastapi import APIRouter

router = APIRouter()


@router.post("/rewrite", summary="Resume bullet rewriting (Phase 2)")
async def rewrite_placeholder():
    return {"detail": "Not implemented in Phase 1.", "phase": 2}
