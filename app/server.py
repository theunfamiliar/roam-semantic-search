from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import search, reindex, health
from app.config import API_TITLE, API_VERSION, CORS_ORIGINS
from app.utils.logging import setup_logging

# Set up logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(reindex.router, prefix="/api/v1", tags=["reindex"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

# Root health check endpoint
@app.get("/", tags=["health"])
async def root():
    return {"status": "running"}

@app.get("/ping", tags=["health"])
async def ping():
    return {"ping": "pong"} 