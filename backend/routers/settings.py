# =============================================================================
# routers/settings.py - Settings Configuration Endpoints
# =============================================================================
# This router handles application settings like:
# - Number of periods per day
# - Current academic year and semester
# - Cycle length (default 10 for Week A/B)
# - Cycle start date (for calculating which day of the cycle any date falls on)
#
# The settings use a "single row" pattern - there's only ever one row in the
# settings table, which we create on first access and update thereafter.
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Import database dependency
from database import get_db

# Import our SQLAlchemy model and Pydantic schemas
from models import Settings
from schemas import SettingsResponse, SettingsUpdate

# -----------------------------------------------------------------------------
# Create the Router
# -----------------------------------------------------------------------------
# APIRouter is like a mini FastAPI app. We define routes here, then include
# this router in the main app. This keeps our code organised by feature.
#
# - prefix: All routes in this router will start with "/settings"
# - tags: Groups these endpoints together in the API documentation
# -----------------------------------------------------------------------------
router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)


# -----------------------------------------------------------------------------
# Helper: Get or Create Settings
# -----------------------------------------------------------------------------
# Since we use the single-row pattern, we need a helper that:
# 1. Tries to get the existing settings row
# 2. Creates a default row if none exists
#
# This is called at the start of both GET and PUT operations.
# -----------------------------------------------------------------------------
def get_or_create_settings(db: Session) -> Settings:
    """
    Retrieve the settings row, creating it with defaults if it doesn't exist.

    This ensures we always have a settings row to work with, even on first run.

    Args:
        db: The database session

    Returns:
        The Settings model instance
    """
    # Try to get the first (and only) settings row
    settings = db.query(Settings).first()

    if settings is None:
        # No settings exist yet - create with defaults
        # The defaults are defined in the model (periods_per_day=6, etc.)
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)  # Reload to get the auto-generated id

    return settings


# =============================================================================
# GET /settings - Retrieve Current Settings
# =============================================================================
@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """
    Get the current application settings.

    Returns the configuration values including:
    - periods_per_day: How many periods in each school day (default: 6)
    - current_year: The academic year (e.g., 2025)
    - current_semester: Which semester (1 or 2)
    - cycle_length: Days in the timetable cycle (default: 10)
    - cycle_start_date: When Day 1 of the cycle begins

    If no settings exist, creates default settings and returns them.
    """
    settings = get_or_create_settings(db)
    return settings


# =============================================================================
# PUT /settings - Update Settings
# =============================================================================
@router.put("", response_model=SettingsResponse)
def update_settings(
    settings_update: SettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update application settings.

    Only the fields you provide will be updated. For example, to just change
    the number of periods per day:

    ```json
    {
        "periods_per_day": 5
    }
    ```

    To set the cycle start date (important for Week A/B calculation):

    ```json
    {
        "cycle_start_date": "2025-01-27"
    }
    ```

    This should be set to the Monday of Week A at the start of term.
    """
    # Get existing settings (or create if first time)
    settings = get_or_create_settings(db)

    # -------------------------------------------------------------------------
    # Update only the fields that were provided
    # -------------------------------------------------------------------------
    # model_dump(exclude_unset=True) returns only the fields that were
    # explicitly set in the request. This lets us do partial updates -
    # fields not in the request keep their existing values.
    # -------------------------------------------------------------------------
    update_data = settings_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        # setattr(obj, "field_name", value) is equivalent to obj.field_name = value
        setattr(settings, field, value)

    # Save changes to database
    db.commit()
    db.refresh(settings)

    return settings


# =============================================================================
# Additional Endpoint: Quick Period Configuration
# =============================================================================
@router.put("/periods", response_model=SettingsResponse)
def set_periods_per_day(
    periods: int,
    db: Session = Depends(get_db)
):
    """
    Quick endpoint to set just the number of periods per day.

    This is a convenience endpoint for the common task of configuring
    how many periods are in each school day.

    Args:
        periods: Number of periods (typically 5-6 for Victorian schools)

    Example:
        PUT /settings/periods?periods=5
    """
    if periods < 1 or periods > 12:
        raise HTTPException(
            status_code=400,
            detail="Periods per day must be between 1 and 12"
        )

    settings = get_or_create_settings(db)
    settings.periods_per_day = periods
    db.commit()
    db.refresh(settings)

    return settings
