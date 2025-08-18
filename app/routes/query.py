from fastapi import APIRouter, HTTPException
from app.schemas.query import QueryIn, QueryOut, QueryHit
from app.services.search_service import search

router = APIRouter(tags=["search"])

@router.post("/query", response_model=QueryOut)
def query_endpoint(payload: QueryIn):
    q = payload.query.strip()
    if not q:
        raise HTTPException(400, "Empty query")
    try:
        hits = search(q, payload.top_k)
        return {"query": q, "results": [QueryHit(**h) for h in hits]}
    except Exception as e:
        raise HTTPException(500, str(e))
