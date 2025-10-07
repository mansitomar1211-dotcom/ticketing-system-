# api/main.py
"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.settings import api_settings
from .database import ticket_db
from .middleware import NetworkSimulationMiddleware
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    ticket_db.initialize_sample_data()
    yield
    # Shutdown
    ticket_db.clear()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=api_settings.title,
        description=api_settings.description,
        version=api_settings.version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add network simulation middleware
    app.add_middleware(NetworkSimulationMiddleware)
    
    # Include routes
    app.include_router(router, prefix="", tags=["tickets"])
    
    return app


# Create the app instance
app = create_app()


def main():
    """Run the application."""
    uvicorn.run(
        "api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=api_settings.debug
    )


if __name__ == "__main__":
    main()