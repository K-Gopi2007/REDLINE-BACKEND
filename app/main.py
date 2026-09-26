from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import auth, contracts

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://redline-lac-ten.vercel.app",
    "https://redline-frontend-psi.vercel.app",
    "https://redline-frontend-git-main-spideyak777-3959s-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
