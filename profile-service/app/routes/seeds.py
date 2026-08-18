from fastapi import APIRouter, Request, Query

router = APIRouter()


@router.get("/seeds")
async def get_seeds(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
):
    db = request.app.state.db
    seeds = await db.get_seeds(limit)
    return {"code": 0, "data": seeds, "total": len(seeds), "msg": "ok"}