from fastapi import APIRouter
router = APIRouter()
@router.post("/forward")
def run_forward(): return {}
@router.post("/backward")
def run_backward(): return {}
