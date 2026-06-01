from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import init_db
from .routers import auth, candidates
from .services.candidate_service import seed_admin, seed_sample_candidates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_admin()
    await seed_sample_candidates()
    yield


app = FastAPI(title="TechKraft Candidate Scoring API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(candidates.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
