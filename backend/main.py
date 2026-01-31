# =============================================================================
# main.py - FastAPI Application Entry Point
# =============================================================================
# This is the main file that runs the Teacher Planner API server.
# It initializes the FastAPI application and sets up the database.
#
# To run the server:
#   cd backend
#   pip install -r requirements.txt
#   uvicorn main:app --reload
#
# The --reload flag enables auto-restart when you change code (dev only).
# The server will be available at: http://localhost:8000
# API docs will be at: http://localhost:8000/docs (Swagger UI)
# =============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our database components
from database import engine, Base

# Import all models so SQLAlchemy knows about them when creating tables.
# Even though we don't use these imports directly here, they must be imported
# so that Base.metadata includes all the table definitions.
from models import Settings, Subject, Lesson, Note, Resource, Todo


# -----------------------------------------------------------------------------
# Application Lifespan Handler
# -----------------------------------------------------------------------------
# The lifespan function runs code when the application starts up and shuts down.
# This is the modern way to handle startup/shutdown in FastAPI (replaces the
# deprecated @app.on_event("startup") decorator).
#
# We use this to create all database tables when the app starts.
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.

    Startup:
        - Creates all database tables if they don't exist

    Shutdown:
        - (Currently nothing, but could close connections, etc.)
    """
    # -------------------------------------------------------------------------
    # STARTUP: Create database tables
    # -------------------------------------------------------------------------
    # Base.metadata.create_all() looks at all classes that inherit from Base
    # (our models) and creates the corresponding tables in the database.
    #
    # The 'checkfirst=True' behavior (default) means it won't try to recreate
    # tables that already exist - it only creates missing ones.
    #
    # This is safe to run every time the app starts:
    # - First run: Creates all tables
    # - Subsequent runs: Does nothing (tables already exist)
    # -------------------------------------------------------------------------
    print("🚀 Starting up Teacher Planner API...")
    print("📚 Creating database tables if they don't exist...")

    # Create all tables defined in our models
    Base.metadata.create_all(bind=engine)

    print("✅ Database ready!")
    print("📖 API documentation available at: http://localhost:8000/docs")

    # The 'yield' separates startup from shutdown code
    # Everything before yield runs on startup
    # Everything after yield runs on shutdown
    yield

    # -------------------------------------------------------------------------
    # SHUTDOWN: Cleanup (if needed)
    # -------------------------------------------------------------------------
    print("👋 Shutting down Teacher Planner API...")


# -----------------------------------------------------------------------------
# Create the FastAPI Application
# -----------------------------------------------------------------------------
# FastAPI() creates the main application object. All routes and configuration
# are attached to this object.
# -----------------------------------------------------------------------------
app = FastAPI(
    # The title appears in the auto-generated API documentation
    title="Teacher Planner API",

    # Description shown in the API docs
    description="""
    A self-hosted teacher planner API for Victorian schools.

    ## Features
    - 10-day timetable cycle (Week A/B) support
    - Customizable periods per day
    - Subject management by year and semester
    - Lesson tracking with attached notes, resources, and todos

    ## Clients
    - Web frontend (React)
    - iOS app (SwiftUI) for iPad
    """,

    # Version of your API - useful for tracking changes
    version="0.1.0",

    # Connect the lifespan handler we defined above
    lifespan=lifespan,
)


# -----------------------------------------------------------------------------
# CORS Middleware Configuration
# -----------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) controls which websites/apps can
# access your API. Without this, your React frontend and iOS app would
# be blocked from making requests to the API.
#
# SECURITY NOTE: The current configuration allows all origins ("*").
# This is fine for local development but should be restricted in production
# to only allow your specific frontend URLs.
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # Which origins (domains) can access the API?
    # "*" means any origin - fine for development
    # In production, you'd list specific URLs: ["http://your-frontend.com"]
    allow_origins=["*"],

    # Allow cookies and authentication headers to be sent
    allow_credentials=True,

    # Which HTTP methods are allowed? (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],

    # Which headers can the client send?
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Root Endpoint
# -----------------------------------------------------------------------------
# A simple endpoint to verify the API is running.
# Visit http://localhost:8000/ to see this response.
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    """
    Root endpoint - confirms the API is running.

    Returns a simple welcome message. Useful for:
    - Health checks
    - Verifying the server is accessible
    - Quick testing during development
    """
    return {
        "message": "Welcome to the Teacher Planner API",
        "documentation": "/docs",
        "version": "0.1.0"
    }


# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
# A dedicated health check endpoint for monitoring and Docker health checks.
# This is separate from root so you have a dedicated endpoint for health status.
# -----------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns the current status of the API. This can be extended to check:
    - Database connectivity
    - External service availability
    - Memory/resource usage

    Used by Docker Compose health checks to verify the container is healthy.
    """
    return {
        "status": "healthy",
        "service": "teacher-planner-api"
    }


# =============================================================================
# NEXT STEPS
# =============================================================================
# This is the basic structure. The next phase will add:
#
# 1. Pydantic Schemas (schemas.py)
#    - Define request/response models for data validation
#
# 2. CRUD Operations (crud.py)
#    - Create, Read, Update, Delete functions for each model
#
# 3. API Routes (routers/)
#    - /subjects - Subject management endpoints
#    - /lessons - Lesson management endpoints
#    - /notes, /resources, /todos - Attached items endpoints
#    - /settings - Application settings endpoints
#
# 4. File Upload Handling
#    - Endpoint for uploading resources (PDFs, images, etc.)
#
# =============================================================================
