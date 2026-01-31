# =============================================================================
# database.py - SQLite Database Connection Setup
# =============================================================================
# This module handles all database connection configuration for the Teacher
# Planner application. It uses SQLAlchemy to manage the SQLite database.
#
# KEY CONCEPTS:
# - Engine: The starting point for SQLAlchemy - it manages the database
#   connection pool and dialect (SQLite in our case).
# - SessionLocal: A factory that creates new database sessions. Each session
#   is a "workspace" for database operations.
# - Base: The declarative base class that all our models inherit from.
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -----------------------------------------------------------------------------
# Database URL Configuration
# -----------------------------------------------------------------------------
# SQLite stores the entire database in a single file. The URL format is:
# sqlite:///./filename.db
#
# The three slashes (///) indicate a relative path. So this creates a file
# called 'teacher_planner.db' in the same directory as this script.
#
# For production on Unraid, this path will be mounted to a Docker volume
# to persist data between container restarts.
# -----------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./teacher_planner.db"

# -----------------------------------------------------------------------------
# Create the SQLAlchemy Engine
# -----------------------------------------------------------------------------
# The engine is the core interface to the database. It maintains a pool of
# connections that can be reused.
#
# IMPORTANT: connect_args={"check_same_thread": False}
# SQLite by default only allows the thread that created a connection to use it.
# FastAPI uses multiple threads to handle requests, so we need to disable this
# check. This is safe because SQLAlchemy's session handling ensures thread
# safety at a higher level.
# -----------------------------------------------------------------------------
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
    echo=False,  # Set to True to see all SQL statements in the console (useful for debugging)
)

# -----------------------------------------------------------------------------
# Create a Session Factory
# -----------------------------------------------------------------------------
# sessionmaker() creates a class that will produce new Session objects when
# called. Think of a Session as a "staging zone" for all the objects you've
# loaded or associated with it during its lifespan.
#
# - autocommit=False: Changes aren't automatically saved. You must explicitly
#   call session.commit() to save changes. This gives you control over
#   transactions and lets you rollback if something goes wrong.
#
# - autoflush=False: SQLAlchemy won't automatically synchronise the session
#   state with the database before queries. We'll manage this manually for
#   more predictable behaviour.
#
# - bind=engine: Associates this session factory with our database engine.
# -----------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# -----------------------------------------------------------------------------
# Create the Declarative Base
# -----------------------------------------------------------------------------
# The declarative_base() function returns a base class that our model classes
# will inherit from. This base class:
#
# 1. Maintains a catalog of all model classes (tables) in our application
# 2. Provides the metadata needed to create tables in the database
# 3. Gives each model class the ability to define columns, relationships, etc.
#
# When we later call Base.metadata.create_all(bind=engine), SQLAlchemy will
# look at all classes that inherit from Base and create corresponding tables.
# -----------------------------------------------------------------------------
Base = declarative_base()


# -----------------------------------------------------------------------------
# Dependency for FastAPI Routes
# -----------------------------------------------------------------------------
# This function is a "dependency" that FastAPI will inject into route handlers.
# It creates a new database session for each request, ensuring that:
#
# 1. Each request gets its own isolated session (no cross-request contamination)
# 2. The session is properly closed after the request completes (even if errors occur)
#
# The 'yield' keyword makes this a generator function. FastAPI uses this pattern:
# - Code before 'yield' runs before the route handler
# - The yielded value (db session) is passed to the route handler
# - Code after 'yield' runs after the route handler completes (cleanup)
#
# Usage in a route:
#   @app.get("/items")
#   def read_items(db: Session = Depends(get_db)):
#       # 'db' is now a session you can use for database operations
#       pass
# -----------------------------------------------------------------------------
def get_db():
    """
    Dependency function that provides a database session to FastAPI routes.

    Yields:
        Session: A SQLAlchemy database session.

    Example:
        @app.get("/subjects")
        def get_subjects(db: Session = Depends(get_db)):
            return db.query(Subject).all()
    """
    # Create a new session instance
    db = SessionLocal()
    try:
        # Yield the session to the route handler
        yield db
    finally:
        # Always close the session when done, even if an error occurred.
        # This releases the database connection back to the pool.
        db.close()
