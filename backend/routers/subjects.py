# =============================================================================
# routers/subjects.py - Subject Management Endpoints
# =============================================================================
# This router handles CRUD operations for Subjects.
# A Subject represents a class you teach, like "Year 11 Modern History".
#
# Endpoints:
# - GET /subjects - List all subjects (with optional filters)
# - POST /subjects - Create a new subject
# - GET /subjects/{id} - Get a specific subject
# - PUT /subjects/{id} - Update a subject
# - DELETE /subjects/{id} - Delete a subject
# =============================================================================

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Subject
from schemas import SubjectCreate, SubjectUpdate, SubjectResponse

# -----------------------------------------------------------------------------
# Create the Router
# -----------------------------------------------------------------------------
router = APIRouter(
    prefix="/subjects",
    tags=["subjects"],
)


# =============================================================================
# GET /subjects - List All Subjects
# =============================================================================
@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    # Query parameters for filtering
    academic_year: Optional[int] = Query(None, description="Filter by academic year"),
    semester: Optional[int] = Query(None, description="Filter by semester (1 or 2)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    year_level: Optional[int] = Query(None, description="Filter by year level (9, 10, 11, 12)"),
    db: Session = Depends(get_db)
):
    """
    List all subjects, optionally filtered.

    Filters can be combined. For example:
    - GET /subjects?academic_year=2025&semester=1
    - GET /subjects?is_active=true&year_level=11

    Returns subjects ordered by year level, then name.
    """
    # Start with a base query
    query = db.query(Subject)

    # Apply filters if provided
    # Each filter is only applied if the parameter was included in the request
    if academic_year is not None:
        query = query.filter(Subject.academic_year == academic_year)

    if semester is not None:
        query = query.filter(Subject.semester == semester)

    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)

    if year_level is not None:
        query = query.filter(Subject.year_level == year_level)

    # Order by year level (nulls last), then by name
    subjects = query.order_by(Subject.year_level, Subject.name).all()

    return subjects


# =============================================================================
# POST /subjects - Create a New Subject
# =============================================================================
@router.post("", response_model=SubjectResponse, status_code=201)
def create_subject(
    subject_data: SubjectCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new subject.

    Required fields:
    - name: The subject name (e.g., "Year 11 Modern History")
    - academic_year: The year (e.g., 2025)
    - semester: Which semester (1 or 2)

    Optional fields:
    - code: Short code (e.g., "11HIST")
    - year_level: Student year level (9, 10, 11, 12)
    - room: Default classroom
    - colour: Hex colour code for UI (e.g., "#FF5733")
    - notes: Any additional notes
    - is_active: Whether the subject is currently active (default: true)

    Example request body:
    ```json
    {
        "name": "Year 11 Modern History",
        "code": "11HIST",
        "year_level": 11,
        "academic_year": 2025,
        "semester": 1,
        "room": "H12",
        "colour": "#3B82F6"
    }
    ```
    """
    # Create a new Subject instance from the request data
    # model_dump() converts the Pydantic model to a dictionary
    # **dict unpacks it as keyword arguments to Subject()
    subject = Subject(**subject_data.model_dump())

    # Add to session and save
    db.add(subject)
    db.commit()

    # Refresh to get auto-generated fields (id, created_at, updated_at)
    db.refresh(subject)

    return subject


# =============================================================================
# GET /subjects/{subject_id} - Get a Specific Subject
# =============================================================================
@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific subject by ID.

    Returns 404 if the subject doesn't exist.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail=f"Subject with id {subject_id} not found"
        )

    return subject


# =============================================================================
# PUT /subjects/{subject_id} - Update a Subject
# =============================================================================
@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a subject.

    Only fields included in the request will be updated.
    Fields not included will keep their existing values.

    Example - just update the room:
    ```json
    {
        "room": "H15"
    }
    ```

    Example - deactivate a subject (soft delete):
    ```json
    {
        "is_active": false
    }
    ```
    """
    # Find the subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail=f"Subject with id {subject_id} not found"
        )

    # Update only provided fields
    update_data = subject_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(subject, field, value)

    db.commit()
    db.refresh(subject)

    return subject


# =============================================================================
# DELETE /subjects/{subject_id} - Delete a Subject
# =============================================================================
@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a subject permanently.

    WARNING: This will also delete all lessons associated with this subject
    (due to the cascade delete relationship).

    Consider using PUT to set is_active=false for a soft delete instead,
    which preserves the subject and its lessons for historical reference.

    Returns 204 No Content on success.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail=f"Subject with id {subject_id} not found"
        )

    db.delete(subject)
    db.commit()

    # Return nothing (204 No Content)
    return None
