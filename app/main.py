from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import auth, contracts

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(contracts.router, prefix=f"{settings.API_V1_STR}/contracts", tags=["Contracts"])

@app.get("/", tags=["Root"])
def root():
    return {
        "name": "Redline",
        "description": "Autonomous Contract Intelligence API",
        "status": "running",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
