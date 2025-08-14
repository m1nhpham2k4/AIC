from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.routes.keyframes import router as keyframes_router
from app.config import FRONTEND_URL

app = FastAPI(title="Keyframes API")

# Cho phép FE gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "*"],  # dev thì mở *, prod thì fix domain FE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(keyframes_router)

# "/" => chuyển hướng sang Node dev (http://localhost:3000/)
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(FRONTEND_URL + "/")

# Health
@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}
