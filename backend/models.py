# =============================================================================
# models.py - SQLAlchemy Database Models
# =============================================================================
# This module defines all the database tables for the Teacher Planner app.
# Each class represents a table in the SQLite database.
#
# RELATIONSHIP OVERVIEW:
# ----------------------
#
#   Settings (standalone - stores app configuration)
#       |
#       v
#   Subject (e.g., "Year 11 History - 2025")
#       |
#       | (one Subject can have many Lessons)
#       v
#   Lesson (the CORE entity - links a Date + Period + Subject)
#       |
#       | (one Lesson can have many Notes, Resources, and Todos)
#       +---> Note
#       +---> Resource
#       +---> Todo
#
# =============================================================================

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Import Base from our database module - all models inherit from this
from database import Base


# =============================================================================
# SETTINGS MODEL
# =============================================================================
# Stores application-wide configuration. Using a single-row table pattern
# where we always read/update row with id=1. This is simpler than using
# environment variables or config files for user-adjustable settings.
# =============================================================================

class Settings(Base):
    """
    Application settings stored in the database.

    This allows the user to customise how the planner works, such as
    how many periods are in each school day. These settings can be
    changed through the UI without restarting the server.

    We use a single-row pattern: there's only ever one row (id=1) in this
    table, which we update as needed.
    """
    # The __tablename__ tells SQLAlchemy what to call this table in the database
    __tablename__ = "settings"

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    # Every table needs a primary key - a unique identifier for each row.
    # 'id' is conventional. 'autoincrement=True' means SQLite will automatically
    # assign the next available number when we insert a new row.
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Customisable Settings
    # -------------------------------------------------------------------------

    # How many periods (class times) are in each school day?
    # Victorian schools typically have 5-6 periods, but this is configurable.
    # 'default=6' means if we don't specify a value, it will be 6.
    periods_per_day: Mapped[int] = mapped_column(Integer, default=6, nullable=False)

    # The current academic year (e.g., 2025).
    # Used as a default when creating new subjects.
    current_year: Mapped[int] = mapped_column(Integer, default=2025, nullable=False)

    # Which semester are we in? (1 or 2, or could be extended for trimesters)
    current_semester: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # The number of days in the timetable cycle.
    # Victorian schools often use a 10-day cycle (Week A and Week B).
    cycle_length: Mapped[int] = mapped_column(Integer, default=10, nullable=False)


# =============================================================================
# SUBJECT MODEL
# =============================================================================
# Represents a subject/class you teach, like "Year 11 History" or
# "Year 9 English - Period 3". Subjects are tied to a specific year
# and semester so you can archive old subjects while keeping their data.
# =============================================================================

class Subject(Base):
    """
    A subject or class being taught.

    Examples:
        - "Year 11 Modern History"
        - "Year 9 English - 9C"
        - "Year 12 Literature"

    Subjects are linked to a specific year and semester, allowing you to:
    - Keep historical data from previous years
    - Set up next semester's subjects in advance
    - Filter views to show only current subjects
    """
    __tablename__ = "subjects"

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Subject Information
    # -------------------------------------------------------------------------

    # The name of the subject (e.g., "Year 11 Modern History")
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Optional: A short code for quick reference (e.g., "11HIST", "9ENG-C")
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # The year level (e.g., 9, 10, 11, 12)
    # Using Integer so we can sort and filter easily
    year_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # The academic year this subject belongs to (e.g., 2025)
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Which semester? (1 or 2). Some subjects run all year (could use 0 for "full year")
    semester: Mapped[int] = mapped_column(Integer, nullable=False)

    # Optional: The room where this class is usually held
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Optional: Colour for UI display (hex code like "#FF5733")
    # Useful for distinguishing subjects in the timetable view
    colour: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    # Optional: Any additional notes about this subject
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Is this subject currently active? Allows "soft delete" - hiding without removing
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    # Track when records are created and modified - useful for debugging
    # and potentially for sync conflict resolution with the iOS app
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,  # Automatically updates when row is modified
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    # This defines the ONE side of a One-to-Many relationship.
    # One Subject can have MANY Lessons.
    #
    # 'back_populates' creates a bidirectional relationship:
    # - From Subject, you can access subject.lessons to get all lessons
    # - From Lesson, you can access lesson.subject to get the subject
    #
    # 'cascade="all, delete-orphan"' means:
    # - If we delete a Subject, all its Lessons are also deleted
    # - This prevents orphaned records (lessons with no subject)
    # -------------------------------------------------------------------------
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="subject",
        cascade="all, delete-orphan"
    )


# =============================================================================
# LESSON MODEL (THE CORE ENTITY)
# =============================================================================
# A Lesson represents a specific teaching instance: what you're teaching,
# on what date, during which period. This is the central entity that
# connects everything together.
#
# Think of it as: "On [date], during period [number], I'm teaching [subject]"
# All notes, resources, and todos are attached to specific lessons.
# =============================================================================

class Lesson(Base):
    """
    The core entity of the planner - a specific lesson instance.

    A Lesson connects:
    - A specific calendar date
    - A specific period number (1-6, or however many periods per day)
    - A specific subject being taught

    All attachable items (notes, resources, todos) link to Lessons.

    Example:
        Lesson(date="2025-02-03", period=3, subject_id=1)
        This means: On February 3rd, 2025, during period 3,
        teaching the subject with id=1 (e.g., "Year 11 History")
    """
    __tablename__ = "lessons"

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Core Lesson Data
    # -------------------------------------------------------------------------

    # The calendar date of this lesson
    # Using SQLAlchemy's Date type which maps to Python's datetime.date
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Which period of the day (e.g., 1, 2, 3, 4, 5, 6)
    # This corresponds to the time slots in your school's timetable
    period: Mapped[int] = mapped_column(Integer, nullable=False)

    # -------------------------------------------------------------------------
    # FOREIGN KEY: Link to Subject
    # -------------------------------------------------------------------------
    # This is how we connect a Lesson to its Subject.
    #
    # HOW FOREIGN KEYS WORK:
    # ----------------------
    # A foreign key is a column that references the primary key of another table.
    # Here, 'subject_id' stores the 'id' value from the 'subjects' table.
    #
    # Example:
    #   If we have a Subject with id=1 (name="Year 11 History"),
    #   and we create a Lesson with subject_id=1,
    #   then that Lesson is linked to "Year 11 History".
    #
    # The database enforces this relationship:
    #   - You can't set subject_id to a value that doesn't exist in subjects.id
    #   - This is called "referential integrity"
    #
    # ForeignKey("subjects.id") tells SQLAlchemy:
    #   "This column's value must match an 'id' in the 'subjects' table"
    # -------------------------------------------------------------------------
    subject_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subjects.id"),  # References the 'id' column in 'subjects' table
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Optional Lesson-Specific Data
    # -------------------------------------------------------------------------

    # Optional: What cycle day is this? (1-10 for Week A/B system)
    # This helps with timetable mapping but can be calculated from the date
    cycle_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Optional: Title or topic for this specific lesson
    # e.g., "World War I - Causes" or "Essay Writing Workshop"
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    # Link back to the Subject (MANY-to-ONE)
    # Many Lessons can belong to one Subject
    subject: Mapped["Subject"] = relationship("Subject", back_populates="lessons")

    # One Lesson can have MANY Notes (ONE-to-MANY)
    notes: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="lesson",
        cascade="all, delete-orphan"  # Delete notes if lesson is deleted
    )

    # One Lesson can have MANY Resources (ONE-to-MANY)
    resources: Mapped[List["Resource"]] = relationship(
        "Resource",
        back_populates="lesson",
        cascade="all, delete-orphan"
    )

    # One Lesson can have MANY Todos (ONE-to-MANY)
    todos: Mapped[List["Todo"]] = relationship(
        "Todo",
        back_populates="lesson",
        cascade="all, delete-orphan"
    )


# =============================================================================
# NOTE MODEL
# =============================================================================
# Notes attached to lessons - for lesson plans, observations, reflections, etc.
# =============================================================================

class Note(Base):
    """
    A note attached to a specific lesson.

    Use cases:
    - Lesson plan / what to teach
    - Post-lesson reflection on what worked
    - Observations about student engagement
    - Things to remember for next time

    Notes have a One-to-Many relationship with Lessons:
    One Lesson can have many Notes, but each Note belongs to exactly one Lesson.
    """
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # FOREIGN KEY: Link to Lesson
    # -------------------------------------------------------------------------
    # This is how a Note gets connected to a specific Lesson.
    #
    # HOW THIS WORKS:
    # ---------------
    # When you create a Note, you must provide a lesson_id value.
    # This value must match the 'id' of an existing Lesson.
    #
    # Example:
    #   1. You have a Lesson with id=42 (Feb 3rd, Period 3, Year 11 History)
    #   2. You create a Note with lesson_id=42, content="Great discussion today!"
    #   3. The Note is now linked to that specific lesson.
    #   4. When you query the Lesson, you can access lesson.notes to see this Note.
    #   5. When you query the Note, you can access note.lesson to see the Lesson.
    # -------------------------------------------------------------------------
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lessons.id"),  # Must match an 'id' in the 'lessons' table
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Note Content
    # -------------------------------------------------------------------------

    # Optional title for the note (e.g., "Lesson Plan", "Reflection")
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # The actual note content - using Text type for longer content
    # Text has no length limit (unlike String which has a max length)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Relationship back to Lesson
    # -------------------------------------------------------------------------
    # This creates the other side of the bidirectional relationship.
    # 'back_populates="notes"' must match the relationship name in Lesson.
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="notes")


# =============================================================================
# RESOURCE MODEL
# =============================================================================
# Resources attached to lessons - links, file references, materials, etc.
# =============================================================================

class Resource(Base):
    """
    A resource attached to a specific lesson.

    Use cases:
    - Links to online resources, videos, articles
    - References to uploaded files (PDFs, worksheets)
    - Textbook page references
    - Links to curriculum documents

    Like Notes, Resources have a One-to-Many relationship with Lessons.
    """
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # FOREIGN KEY: Link to Lesson
    # -------------------------------------------------------------------------
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lessons.id"),
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Resource Details
    # -------------------------------------------------------------------------

    # Title/name of the resource (e.g., "WWI Documentary", "Chapter 5 Worksheet")
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # URL if it's a web resource
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # File path if it's an uploaded file (relative to upload directory)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Type of resource for filtering/display (e.g., "link", "pdf", "video", "image")
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Optional description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Relationship back to Lesson
    # -------------------------------------------------------------------------
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="resources")


# =============================================================================
# TODO MODEL
# =============================================================================
# Actionable items attached to lessons - things to do before, during, or after.
# =============================================================================

class Todo(Base):
    """
    A to-do item attached to a specific lesson.

    Use cases:
    - "Return marked essays to students"
    - "Print worksheets for activity"
    - "Email parent about Johnny's progress"
    - "Prepare quiz for next lesson"

    Todos have completion tracking so you can mark them as done.
    Like Notes and Resources, Todos have a One-to-Many relationship with Lessons.

    FOREIGN KEY EXPLANATION:
    ------------------------
    The 'lesson_id' column is a FOREIGN KEY that links each Todo to a Lesson.

    How it works:
    1. When you create a Todo, you set lesson_id to match a Lesson's id
    2. The database enforces that this lesson_id must exist in the lessons table
    3. You can now navigate both directions:
       - todo.lesson -> gets the Lesson object
       - lesson.todos -> gets a list of all Todo objects for that lesson

    This is called a One-to-Many relationship because:
    - ONE Lesson can have MANY Todos
    - But each Todo belongs to exactly ONE Lesson
    """
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # FOREIGN KEY: Link to Lesson
    # -------------------------------------------------------------------------
    # This integer column stores the 'id' of the parent Lesson.
    # The ForeignKey constraint ensures the value exists in lessons.id
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lessons.id"),  # Database-level constraint
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Todo Content
    # -------------------------------------------------------------------------

    # What needs to be done?
    content: Mapped[str] = mapped_column(String(500), nullable=False)

    # Has this been completed?
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # When was it completed? (null if not yet completed)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Optional: Priority level (1=high, 2=medium, 3=low)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Optional: Due date if different from the lesson date
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # -------------------------------------------------------------------------
    # Relationship back to Lesson
    # -------------------------------------------------------------------------
    # This creates the reverse link. When you have a Todo object, you can
    # access todo.lesson to get the Lesson object it belongs to.
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="todos")
