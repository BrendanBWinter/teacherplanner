# =============================================================================
# routers/lessons.py - Lesson and Timetable Endpoints
# =============================================================================
# This router handles:
# - Lesson CRUD operations
# - The critical "Get Lessons by Date Range" endpoint for timetable display
# - Week A/B (cycle day) calculation logic
#
# WEEK A/B CALCULATION EXPLAINED:
# ===============================
# Victorian schools often use a 10-day timetable cycle that spans two weeks:
# - Week A: Days 1-5 (Monday to Friday)
# - Week B: Days 6-10 (Monday to Friday of the following week)
#
# To calculate which cycle day any given date falls on, we need:
# 1. A reference point: cycle_start_date (the Monday when Day 1 begins)
# 2. To count only WORKING DAYS (skip weekends)
# 3. Use modulo to wrap around the cycle
#
# THE ALGORITHM:
# --------------
# 1. Start from cycle_start_date (should be a Monday, Day 1 of Week A)
# 2. For any target date, count the number of working days between them
# 3. cycle_day = (working_days_count % cycle_length) + 1
# 4. If cycle_day is 1-5 → Week A; if 6-10 → Week B
#
# EXAMPLE:
# --------
# cycle_start_date = Monday, Jan 27, 2025 (Day 1)
# Target date = Monday, Feb 3, 2025
# Working days between: 5 (Tue, Wed, Thu, Fri, and then Mon = days passed)
# Actually: Jan 27 is day 0 (start), Jan 28-31 = 4 days, Feb 3 = day 5
# cycle_day = (5 % 10) + 1 = 6 → Week B, Day 1 of Week B
#
# IMPORTANT NOTES:
# ----------------
# - Weekends are automatically skipped (Saturday=5, Sunday=6 in weekday())
# - Public holidays would need a separate "holidays" table (future enhancement)
# - If cycle_start_date is not set, we default to showing cycle_day as 0
# =============================================================================

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Lesson, Subject, Settings
from schemas import (
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    LessonDetailResponse,
    DayInfo,
    WeekTimetable,
)

# -----------------------------------------------------------------------------
# Create the Router
# -----------------------------------------------------------------------------
router = APIRouter(
    prefix="/lessons",
    tags=["lessons"],
)


# =============================================================================
# WEEK A/B CALCULATION FUNCTIONS
# =============================================================================

def count_working_days_between(start_date: date, end_date: date) -> int:
    """
    Count the number of working days (Monday-Friday) between two dates.

    This is used to calculate the cycle day for any given date.
    The start_date is considered day 0, and we count forward to end_date.

    Args:
        start_date: The reference date (cycle start date)
        end_date: The date we want to find the cycle day for

    Returns:
        The number of working days between the dates.
        Returns negative if end_date is before start_date.

    Example:
        start = Monday Jan 27
        end = Monday Feb 3
        Returns: 5 (Tue, Wed, Thu, Fri of week 1, plus Mon of week 2)

    Note: We count the days AFTER start_date up to and including end_date.
    """
    if end_date < start_date:
        # Handle dates before the cycle start
        # We count backwards (negative working days)
        return -count_working_days_between(end_date, start_date)

    if end_date == start_date:
        return 0

    working_days = 0
    current = start_date

    # Move through each day from start to end
    while current < end_date:
        current += timedelta(days=1)
        # weekday() returns 0=Monday through 6=Sunday
        # We only count Monday (0) through Friday (4)
        if current.weekday() < 5:  # 0-4 = Monday-Friday
            working_days += 1

    return working_days


def calculate_cycle_day(
    target_date: date,
    cycle_start_date: date,
    cycle_length: int = 10
) -> int:
    """
    Calculate which day of the timetable cycle a given date falls on.

    Args:
        target_date: The date to calculate the cycle day for
        cycle_start_date: The Monday when Day 1 of the cycle begins
        cycle_length: Total days in the cycle (default 10 for Week A/B)

    Returns:
        The cycle day (1 to cycle_length)
        For a 10-day cycle: 1-5 = Week A, 6-10 = Week B

    Example:
        cycle_start = Jan 27 (Monday, Day 1)
        target = Feb 3 (Monday, one week later)
        working_days = 5
        cycle_day = (5 % 10) + 1 = 6 → First day of Week B
    """
    # Count working days from cycle start to target
    working_days = count_working_days_between(cycle_start_date, target_date)

    # Use modulo to wrap around the cycle
    # Add 1 because we want days numbered 1-10, not 0-9
    cycle_day = (working_days % cycle_length) + 1

    return cycle_day


def get_week_label(cycle_day: int, cycle_length: int = 10) -> tuple[bool, str]:
    """
    Determine if a cycle day is in Week A or Week B.

    Args:
        cycle_day: The day number in the cycle (1-10)
        cycle_length: Total days in the cycle (default 10)

    Returns:
        A tuple of (is_week_a: bool, label: str)
        e.g., (True, "Week A") or (False, "Week B")
    """
    # For a 10-day cycle, the midpoint is 5
    # Days 1-5 are Week A, Days 6-10 are Week B
    midpoint = cycle_length // 2

    is_week_a = cycle_day <= midpoint
    label = "Week A" if is_week_a else "Week B"

    return is_week_a, label


def get_weekday_name(weekday: int) -> str:
    """Convert weekday number (0-6) to name."""
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[weekday]


# =============================================================================
# GET /lessons/week - Get Timetable for a Week (THE CRITICAL ENDPOINT)
# =============================================================================
@router.get("/week", response_model=WeekTimetable)
def get_week_timetable(
    start_date: date = Query(..., description="Start date (should be a Monday)"),
    db: Session = Depends(get_db)
):
    """
    Get the timetable for a week, including Week A/B information.

    This is the primary endpoint for displaying the planner view.
    It returns:
    - Each day of the week with its cycle day (1-10)
    - Whether each day is Week A or Week B
    - All lessons for each day with their notes, resources, and todos

    WEEK A/B CALCULATION:
    ---------------------
    The cycle day is calculated based on the cycle_start_date in Settings.
    If cycle_start_date is not set, all days will show cycle_day=0.

    To set up Week A/B:
    1. PUT /settings with cycle_start_date set to the Monday of Week A
       at the start of term (e.g., "2025-01-27")
    2. The system will then calculate the correct cycle day for any date

    Example response for a Week B:
    ```json
    {
        "week_start": "2025-02-03",
        "week_end": "2025-02-07",
        "primary_week": "Week B",
        "periods_per_day": 6,
        "days": [
            {
                "date": "2025-02-03",
                "weekday": 0,
                "weekday_name": "Monday",
                "cycle_day": 6,
                "is_week_a": false,
                "week_label": "Week B",
                "lessons": [...]
            },
            ...
        ]
    }
    ```
    """
    # -------------------------------------------------------------------------
    # Step 1: Get settings for cycle calculation
    # -------------------------------------------------------------------------
    settings = db.query(Settings).first()

    # Default values if settings don't exist
    cycle_start_date = settings.cycle_start_date if settings else None
    cycle_length = settings.cycle_length if settings else 10
    periods_per_day = settings.periods_per_day if settings else 6

    # -------------------------------------------------------------------------
    # Step 2: Calculate the week boundaries
    # -------------------------------------------------------------------------
    # Ensure start_date is a Monday (weekday 0)
    # If not, adjust back to the previous Monday
    days_since_monday = start_date.weekday()
    week_start = start_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=4)  # Friday

    # -------------------------------------------------------------------------
    # Step 3: Fetch all lessons for this week
    # -------------------------------------------------------------------------
    # We use 'joinedload' to eagerly load related data in a single query.
    # This avoids the "N+1 query problem" where we'd otherwise make separate
    # queries for each lesson's notes, resources, todos, and subject.
    lessons = (
        db.query(Lesson)
        .options(
            joinedload(Lesson.subject),
            joinedload(Lesson.notes),
            joinedload(Lesson.resources),
            joinedload(Lesson.todos),
        )
        .filter(Lesson.date >= week_start)
        .filter(Lesson.date <= week_end)
        .order_by(Lesson.date, Lesson.period)
        .all()
    )

    # -------------------------------------------------------------------------
    # Step 4: Organize lessons by date
    # -------------------------------------------------------------------------
    # Create a dictionary mapping date -> list of lessons
    lessons_by_date = {}
    for lesson in lessons:
        if lesson.date not in lessons_by_date:
            lessons_by_date[lesson.date] = []
        lessons_by_date[lesson.date].append(lesson)

    # -------------------------------------------------------------------------
    # Step 5: Build the response with cycle day info for each day
    # -------------------------------------------------------------------------
    days = []
    primary_week = "Unknown"

    for i in range(5):  # Monday (0) to Friday (4)
        current_date = week_start + timedelta(days=i)

        # Calculate cycle day for this date
        if cycle_start_date:
            cycle_day = calculate_cycle_day(current_date, cycle_start_date, cycle_length)
            is_week_a, week_label = get_week_label(cycle_day, cycle_length)
        else:
            # No cycle start date configured - show 0 and unknown
            cycle_day = 0
            is_week_a = True
            week_label = "Not configured"

        # Set primary week based on Monday
        if i == 0:
            primary_week = week_label

        # Get lessons for this day (empty list if none)
        day_lessons = lessons_by_date.get(current_date, [])

        # Build the DayInfo object
        day_info = DayInfo(
            date=current_date,
            weekday=current_date.weekday(),
            weekday_name=get_weekday_name(current_date.weekday()),
            cycle_day=cycle_day,
            is_week_a=is_week_a,
            week_label=week_label,
            lessons=day_lessons,  # Pydantic will convert to LessonDetailResponse
        )
        days.append(day_info)

    # -------------------------------------------------------------------------
    # Step 6: Return the complete week timetable
    # -------------------------------------------------------------------------
    return WeekTimetable(
        week_start=week_start,
        week_end=week_end,
        primary_week=primary_week,
        periods_per_day=periods_per_day,
        days=days,
    )


# =============================================================================
# POST /lessons - Create a New Lesson
# =============================================================================
@router.post("", response_model=LessonResponse, status_code=201)
def create_lesson(
    lesson_data: LessonCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new lesson.

    A lesson connects a date, period, and subject.

    Required fields:
    - date: The calendar date (e.g., "2025-02-03")
    - period: Which period of the day (e.g., 3)
    - subject_id: The ID of the subject being taught

    Optional fields:
    - cycle_day: Override the calculated cycle day (usually auto-calculated)
    - title: Topic or title for this specific lesson

    Example:
    ```json
    {
        "date": "2025-02-03",
        "period": 3,
        "subject_id": 1,
        "title": "World War I - Causes"
    }
    ```
    """
    # Verify the subject exists
    subject = db.query(Subject).filter(Subject.id == lesson_data.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=404,
            detail=f"Subject with id {lesson_data.subject_id} not found"
        )

    # Check for duplicate (same date and period)
    existing = (
        db.query(Lesson)
        .filter(Lesson.date == lesson_data.date)
        .filter(Lesson.period == lesson_data.period)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A lesson already exists for {lesson_data.date} period {lesson_data.period}"
        )

    # Auto-calculate cycle_day if not provided
    if lesson_data.cycle_day is None:
        settings = db.query(Settings).first()
        if settings and settings.cycle_start_date:
            calculated_cycle_day = calculate_cycle_day(
                lesson_data.date,
                settings.cycle_start_date,
                settings.cycle_length
            )
            lesson_data_dict = lesson_data.model_dump()
            lesson_data_dict["cycle_day"] = calculated_cycle_day
        else:
            lesson_data_dict = lesson_data.model_dump()
    else:
        lesson_data_dict = lesson_data.model_dump()

    lesson = Lesson(**lesson_data_dict)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson


# =============================================================================
# GET /lessons/{lesson_id} - Get a Specific Lesson with All Details
# =============================================================================
@router.get("/{lesson_id}", response_model=LessonDetailResponse)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific lesson with all its attached notes, resources, and todos.

    This is useful for viewing/editing a single lesson's details.
    """
    lesson = (
        db.query(Lesson)
        .options(
            joinedload(Lesson.subject),
            joinedload(Lesson.notes),
            joinedload(Lesson.resources),
            joinedload(Lesson.todos),
        )
        .filter(Lesson.id == lesson_id)
        .first()
    )

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson with id {lesson_id} not found"
        )

    return lesson


# =============================================================================
# PUT /lessons/{lesson_id} - Update a Lesson
# =============================================================================
@router.put("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: int,
    lesson_update: LessonUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a lesson's basic information.

    Only provided fields will be updated.

    Example - update just the title:
    ```json
    {
        "title": "Updated: WW1 Causes and Effects"
    }
    ```
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson with id {lesson_id} not found"
        )

    update_data = lesson_update.model_dump(exclude_unset=True)

    # If subject_id is being updated, verify it exists
    if "subject_id" in update_data:
        subject = db.query(Subject).filter(Subject.id == update_data["subject_id"]).first()
        if not subject:
            raise HTTPException(
                status_code=404,
                detail=f"Subject with id {update_data['subject_id']} not found"
            )

    for field, value in update_data.items():
        setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)

    return lesson


# =============================================================================
# DELETE /lessons/{lesson_id} - Delete a Lesson
# =============================================================================
@router.delete("/{lesson_id}", status_code=204)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a lesson and all its attached notes, resources, and todos.

    Returns 204 No Content on success.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson with id {lesson_id} not found"
        )

    db.delete(lesson)
    db.commit()

    return None
