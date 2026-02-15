from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import videos, jobs, editor

settings = get_settings()

app = FastAPI(
    title="Enjo-Guardian API",
    description="動画の炎上リスクからあなたを守ります",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.run\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(editor.router, prefix="/api/jobs", tags=["editor"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
