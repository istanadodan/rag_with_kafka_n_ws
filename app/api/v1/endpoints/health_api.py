from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz", operation_id="health_check")
def healthz():
    return {"status": "ok"}
