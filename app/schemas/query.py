from typing import List, Optional
from pydantic import BaseModel, Field

class QueryIn(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(24, ge=1, le=200)

class QueryHit(BaseModel):
    leaf: str
    n: Optional[int] = None        # 1-based frame index (nếu có)
    filename: Optional[str] = None # "001.jpg" (khuyên dùng để map chính xác)
    score: float

class QueryOut(BaseModel):
    query: str
    results: List[QueryHit]
