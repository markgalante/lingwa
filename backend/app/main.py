from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router

tags_metadata = [
    {
        "name": "auth",
        "description": "Authentication: email sign-up flow, Google OAuth, login, and current-user lookup.",
    },
]

app = FastAPI(
    title="Lingwa API",
    version="0.1.0",
    description=(
        "Backend API for Lingwa – an adaptive vocabulary learning app.\n\n"
        "Interactive docs: `/docs` (Swagger UI) · `/redoc` (ReDoc)"
    ),
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/api/health", summary="Health check", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
