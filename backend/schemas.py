# =============================================================================
# schemas.py - Pydantic Models for Request/Response Validation
# =============================================================================
# Pydantic models define the shape of data coming INTO and going OUT OF our API.
# They provide:
# 1. Automatic validation (reject invalid data with helpful error messages)
# 2. Type conversion (e.g., string "2025-02-03" → Python date object)
# 3. Documentation (FastAPI uses these to generate API docs)
#
# NAMING CONVENTION:
# - *Base: Shared fields used by both create and response
# - *Create: Fields needed when creating a new record (request body)
# - *Update: Fields that can be updated (all optional for PATCH requests)
# - *Response: Fields returned by the API (includes id, timestamps, etc.)
# =============================================================================

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# =============================================================================
# SETTINGS SCHEMAS
# =============================================================================

class SettingsBase(BaseModel):
    """
    Base schema for Settings - shared fields.
    """
    periods_per_day: int = 6
    current_year: int = 2025
    current_semester: int = 1
    cycle_length: int = 10
    cycle_start_date: Optional[date] = None


class SettingsUpdate(BaseModel):
    """
    Schema for updating settings. All fields are optional.
    Only provided fields will be updated.
    """
    periods_per_day: Optional[int] = None
    current_year: Optional[int] = None
    current_semester: Optional[int] = None
    cycle_length: Optional[int] = None
    cycle_start_date: Optional[date] = None


class SettingsResponse(SettingsBase):
    """
    Schema for Settings response - includes id.
    """
    id: int

    # Pydantic v2 configuration to work with SQLAlchemy models.
    # 'from_attributes=True' tells Pydantic to read data from object
    # attributes (like SQLAlchemy model instances) not just dictionaries.
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SUBJECT SCHEMAS
# =============================================================================

class SubjectBase(BaseModel):
    """
    Base schema for Subject - shared fields for create and response.
    """
    name: str
    code: Optional[str] = None
    year_level: Optional[int] = None
    academic_year: int
    semester: int
    room: Optional[str] = None
    colour: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class SubjectCreate(SubjectBase):
    """
    Schema for creating a new Subject.
    Inherits all fields from SubjectBase.
    """
    pass


class SubjectUpdate(BaseModel):
    """
    Schema for updating a Subject. All fields optional.
    """
    name: Optional[str] = None
    code: Optional[str] = None
    year_level: Optional[int] = None
    academic_year: Optional[int] = None
    semester: Optional[int] = None
    room: Optional[str] = None
    colour: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SubjectResponse(SubjectBase):
    """
    Schema for Subject response - includes id and timestamps.
    """
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# NOTE SCHEMAS
# =============================================================================

class NoteBase(BaseModel):
    """Base schema for Note."""
    title: Optional[str] = None
    content: str


class NoteCreate(NoteBase):
    """Schema for creating a Note. lesson_id is provided via URL path."""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating a Note."""
    title: Optional[str] = None
    content: Optional[str] = None


class NoteResponse(NoteBase):
    """Schema for Note response."""
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# RESOURCE SCHEMAS
# =============================================================================

class ResourceBase(BaseModel):
    """Base schema for Resource."""
    title: str
    url: Optional[str] = None
    file_path: Optional[str] = None
    resource_type: Optional[str] = None
    description: Optional[str] = None


class ResourceCreate(ResourceBase):
    """Schema for creating a Resource."""
    pass


class ResourceUpdate(BaseModel):
    """Schema for updating a Resource."""
    title: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    resource_type: Optional[str] = None
    description: Optional[str] = None


class ResourceResponse(ResourceBase):
    """Schema for Resource response."""
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# TODO SCHEMAS
# =============================================================================

class TodoBase(BaseModel):
    """Base schema for Todo."""
    content: str
    is_completed: bool = False
    priority: Optional[int] = None
    due_date: Optional[date] = None


class TodoCreate(TodoBase):
    """Schema for creating a Todo."""
    pass


class TodoUpdate(BaseModel):
    """Schema for updating a Todo."""
    content: Optional[str] = None
    is_completed: Optional[bool] = None
    priority: Optional[int] = None
    due_date: Optional[date] = None


class TodoResponse(TodoBase):
    """Schema for Todo response."""
    id: int
    lesson_id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# LESSON SCHEMAS
# =============================================================================

class LessonBase(BaseModel):
    """Base schema for Lesson."""
    date: date
    period: int
    subject_id: int
    cycle_day: Optional[int] = None
    title: Optional[str] = None


class LessonCreate(LessonBase):
    """Schema for creating a Lesson."""
    pass


class LessonUpdate(BaseModel):
    """Schema for updating a Lesson."""
    date: Optional[date] = None
    period: Optional[int] = None
    subject_id: Optional[int] = None
    cycle_day: Optional[int] = None
    title: Optional[str] = None


class LessonResponse(LessonBase):
    """
    Schema for Lesson response - basic info without nested items.
    """
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LessonDetailResponse(LessonResponse):
    """
    Schema for detailed Lesson response - includes all attached items.
    Used when fetching a single lesson with all its notes, resources, and todos.
    """
    notes: List[NoteResponse] = []
    resources: List[ResourceResponse] = []
    todos: List[TodoResponse] = []
    # Include the subject details for convenience
    subject: Optional[SubjectResponse] = None


# =============================================================================
# PLANNER/TIMETABLE SCHEMAS
# =============================================================================
# These schemas are used for the "Get Lessons by Date Range" endpoint.
# They provide structured data for displaying a week's timetable.
# =============================================================================

class DayInfo(BaseModel):
    """
    Information about a single day in the timetable.

    This schema represents one day (e.g., Monday of Week A) with:
    - The actual calendar date
    - Which cycle day it is (1-10)
    - Whether it's Week A or Week B
    - All lessons scheduled for that day
    """
    # The actual calendar date (e.g., 2025-02-03)
    date: date

    # Which day of the week (0=Monday, 4=Friday)
    # Useful for UI layout
    weekday: int

    # Human-readable day name (e.g., "Monday")
    weekday_name: str

    # -------------------------------------------------------------------------
    # CYCLE DAY: The position in the 10-day timetable cycle
    # -------------------------------------------------------------------------
    # In a 10-day cycle:
    # - Days 1-5 are Week A (Monday-Friday of the first week)
    # - Days 6-10 are Week B (Monday-Friday of the second week)
    #
    # This is calculated based on the cycle_start_date in Settings.
    # See routers/lessons.py for the calculation logic.
    # -------------------------------------------------------------------------
    cycle_day: int

    # Is this Week A (True) or Week B (False)?
    # For a 10-day cycle: Week A = days 1-5, Week B = days 6-10
    is_week_a: bool

    # Human-readable week label (e.g., "Week A" or "Week B")
    week_label: str

    # All lessons scheduled for this day, sorted by period
    lessons: List[LessonDetailResponse] = []


class WeekTimetable(BaseModel):
    """
    A full week's timetable data.

    This is the response for the "Get Lessons by Date Range" endpoint.
    It contains:
    - Metadata about the week
    - A list of DayInfo objects for each school day
    """
    # The start date of the week (should be a Monday)
    week_start: date

    # The end date of the week (should be a Friday)
    week_end: date

    # Is this primarily Week A or Week B?
    # (Based on the Monday of the week)
    primary_week: str

    # Number of periods per day (from settings)
    periods_per_day: int

    # The individual days with their lessons
    days: List[DayInfo]
