from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Procurement Agent API...")
    print(f"📊 Debug mode: {settings.debug}")
    yield
    # Shutdown
    print("🛑 Shutting down Procurement Agent API...")


app = FastAPI(
    title="Procurement Agent API",
    description="Multi-agent FastAPI backend for procurement assistance with M365 Teams integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for Teams and frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend
        "http://localhost:8080",  # Alternative frontend
        "https://teams.microsoft.com",  # Teams
        "https://*.teams.microsoft.com",  # Teams subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/agents", tags=["agents"])


@app.get("/")
async def root():
    return {
        "message": "Procurement Agent API is running",
        "version": "1.0.0",
        "features": [
            "Multi-agent RAG system",
            "Supervisor-agent orchestration",
            "Microsoft Teams integration",
            "Azure OpenAI & Search integration"
        ]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "environment": "development" if settings.debug else "production"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
