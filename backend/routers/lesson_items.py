# =============================================================================
# routers/lesson_items.py - Notes, Resources, and Todos Endpoints
# =============================================================================
# This router handles CRUD operations for items attached to lessons:
# - Notes: Lesson plans, reflections, observations
# - Resources: Links, files, materials
# - Todos: Actionable items with completion tracking
#
# All endpoints are nested under /lessons/{lesson_id}/ to make the
# relationship clear. For example:
# - POST /lessons/42/notes - Add a note to lesson 42
# - GET /lessons/42/todos - List all todos for lesson 42
# =============================================================================

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Lesson, Note, Resource, Todo
from schemas import (
    NoteCreate, NoteUpdate, NoteResponse,
    ResourceCreate, ResourceUpdate, ResourceResponse,
    TodoCreate, TodoUpdate, TodoResponse,
)

# -----------------------------------------------------------------------------
# Create the Router
# -----------------------------------------------------------------------------
# Note: This router uses a prefix that includes the lesson_id parameter.
# This creates URLs like /lessons/42/notes, /lessons/42/resources, etc.
# -----------------------------------------------------------------------------
router = APIRouter(
    prefix="/lessons/{lesson_id}",
    tags=["lesson-items"],
)


# -----------------------------------------------------------------------------
# Helper: Verify Lesson Exists
# -----------------------------------------------------------------------------
def get_lesson_or_404(lesson_id: int, db: Session) -> Lesson:
    """
    Fetch a lesson by ID, raising 404 if not found.

    This is called at the start of every endpoint to ensure
    the parent lesson exists before we try to add/modify items.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=404,
            detail=f"Lesson with id {lesson_id} not found"
        )
    return lesson


# =============================================================================
# NOTES ENDPOINTS
# =============================================================================

@router.get("/notes", response_model=List[NoteResponse])
def list_notes(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """
    List all notes for a specific lesson.

    Returns notes ordered by creation date (newest first).
    """
    get_lesson_or_404(lesson_id, db)  # Verify lesson exists

    notes = (
        db.query(Note)
        .filter(Note.lesson_id == lesson_id)
        .order_by(Note.created_at.desc())
        .all()
    )
    return notes


@router.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(
    lesson_id: int,
    note_data: NoteCreate,
    db: Session = Depends(get_db)
):
    """
    Add a note to a lesson.

    Notes can be used for:
    - Lesson plans (what to teach)
    - Post-lesson reflections
    - Observations about student engagement
    - Things to remember for next time

    Example:
    ```json
    {
        "title": "Lesson Plan",
        "content": "1. Warm-up discussion (10 min)\\n2. Video: WW1 causes (15 min)..."
    }
    ```
    """
    get_lesson_or_404(lesson_id, db)

    note = Note(
        lesson_id=lesson_id,
        **note_data.model_dump()
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return note


@router.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(
    lesson_id: int,
    note_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific note."""
    get_lesson_or_404(lesson_id, db)

    note = db.query(Note).filter(
        Note.id == note_id,
        Note.lesson_id == lesson_id
    ).first()

    if not note:
        raise HTTPException(
            status_code=404,
            detail=f"Note with id {note_id} not found for lesson {lesson_id}"
        )

    return note


@router.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    lesson_id: int,
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a note.

    Only provided fields will be updated.

    Example - just update the content:
    ```json
    {
        "content": "Updated lesson plan content..."
    }
    ```
    """
    get_lesson_or_404(lesson_id, db)

    note = db.query(Note).filter(
        Note.id == note_id,
        Note.lesson_id == lesson_id
    ).first()

    if not note:
        raise HTTPException(
            status_code=404,
            detail=f"Note with id {note_id} not found for lesson {lesson_id}"
        )

    update_data = note_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)

    return note


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    lesson_id: int,
    note_id: int,
    db: Session = Depends(get_db)
):
    """Delete a note."""
    get_lesson_or_404(lesson_id, db)

    note = db.query(Note).filter(
        Note.id == note_id,
        Note.lesson_id == lesson_id
    ).first()

    if not note:
        raise HTTPException(
            status_code=404,
            detail=f"Note with id {note_id} not found for lesson {lesson_id}"
        )

    db.delete(note)
    db.commit()

    return None


# =============================================================================
# RESOURCES ENDPOINTS
# =============================================================================

@router.get("/resources", response_model=List[ResourceResponse])
def list_resources(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """
    List all resources for a specific lesson.

    Returns resources ordered by creation date (newest first).
    """
    get_lesson_or_404(lesson_id, db)

    resources = (
        db.query(Resource)
        .filter(Resource.lesson_id == lesson_id)
        .order_by(Resource.created_at.desc())
        .all()
    )
    return resources


@router.post("/resources", response_model=ResourceResponse, status_code=201)
def create_resource(
    lesson_id: int,
    resource_data: ResourceCreate,
    db: Session = Depends(get_db)
):
    """
    Add a resource to a lesson.

    Resources can be:
    - Links to websites, videos, articles
    - References to uploaded files
    - Textbook page numbers
    - Curriculum document links

    Example - a web link:
    ```json
    {
        "title": "WW1 Documentary",
        "url": "https://youtube.com/watch?v=...",
        "resource_type": "video",
        "description": "25-minute overview of WW1 causes"
    }
    ```

    Example - a file reference:
    ```json
    {
        "title": "Chapter 5 Worksheet",
        "file_path": "worksheets/history/ch5_worksheet.pdf",
        "resource_type": "pdf"
    }
    ```
    """
    get_lesson_or_404(lesson_id, db)

    resource = Resource(
        lesson_id=lesson_id,
        **resource_data.model_dump()
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return resource


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
def get_resource(
    lesson_id: int,
    resource_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific resource."""
    get_lesson_or_404(lesson_id, db)

    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.lesson_id == lesson_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {resource_id} not found for lesson {lesson_id}"
        )

    return resource


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
def update_resource(
    lesson_id: int,
    resource_id: int,
    resource_update: ResourceUpdate,
    db: Session = Depends(get_db)
):
    """Update a resource."""
    get_lesson_or_404(lesson_id, db)

    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.lesson_id == lesson_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {resource_id} not found for lesson {lesson_id}"
        )

    update_data = resource_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)

    db.commit()
    db.refresh(resource)

    return resource


@router.delete("/resources/{resource_id}", status_code=204)
def delete_resource(
    lesson_id: int,
    resource_id: int,
    db: Session = Depends(get_db)
):
    """Delete a resource."""
    get_lesson_or_404(lesson_id, db)

    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.lesson_id == lesson_id
    ).first()

    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {resource_id} not found for lesson {lesson_id}"
        )

    db.delete(resource)
    db.commit()

    return None


# =============================================================================
# TODOS ENDPOINTS
# =============================================================================

@router.get("/todos", response_model=List[TodoResponse])
def list_todos(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """
    List all todos for a specific lesson.

    Returns todos ordered by:
    1. Incomplete items first
    2. Then by priority (1=high first)
    3. Then by creation date
    """
    get_lesson_or_404(lesson_id, db)

    todos = (
        db.query(Todo)
        .filter(Todo.lesson_id == lesson_id)
        .order_by(Todo.is_completed, Todo.priority, Todo.created_at)
        .all()
    )
    return todos


@router.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(
    lesson_id: int,
    todo_data: TodoCreate,
    db: Session = Depends(get_db)
):
    """
    Add a todo item to a lesson.

    Todos are actionable items related to the lesson, such as:
    - "Return marked essays to students"
    - "Print worksheets for activity"
    - "Email parent about student progress"
    - "Prepare quiz for next lesson"

    Example:
    ```json
    {
        "content": "Return marked essays to students",
        "priority": 1,
        "due_date": "2025-02-05"
    }
    ```

    Priority levels:
    - 1 = High priority
    - 2 = Medium priority
    - 3 = Low priority
    """
    get_lesson_or_404(lesson_id, db)

    todo = Todo(
        lesson_id=lesson_id,
        **todo_data.model_dump()
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)

    return todo


@router.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(
    lesson_id: int,
    todo_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific todo."""
    get_lesson_or_404(lesson_id, db)

    todo = db.query(Todo).filter(
        Todo.id == todo_id,
        Todo.lesson_id == lesson_id
    ).first()

    if not todo:
        raise HTTPException(
            status_code=404,
            detail=f"Todo with id {todo_id} not found for lesson {lesson_id}"
        )

    return todo


@router.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(
    lesson_id: int,
    todo_id: int,
    todo_update: TodoUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a todo item.

    Common use cases:
    - Mark as completed: `{"is_completed": true}`
    - Update content: `{"content": "Updated task description"}`
    - Change priority: `{"priority": 2}`

    When marking a todo as completed, the system automatically
    records the completion timestamp.
    """
    get_lesson_or_404(lesson_id, db)

    todo = db.query(Todo).filter(
        Todo.id == todo_id,
        Todo.lesson_id == lesson_id
    ).first()

    if not todo:
        raise HTTPException(
            status_code=404,
            detail=f"Todo with id {todo_id} not found for lesson {lesson_id}"
        )

    update_data = todo_update.model_dump(exclude_unset=True)

    # -------------------------------------------------------------------------
    # Handle completion timestamp
    # -------------------------------------------------------------------------
    # When marking a todo as completed, record when it was completed.
    # When un-completing (setting back to false), clear the timestamp.
    # -------------------------------------------------------------------------
    if "is_completed" in update_data:
        if update_data["is_completed"] and not todo.is_completed:
            # Being marked as completed now
            todo.completed_at = datetime.utcnow()
        elif not update_data["is_completed"] and todo.is_completed:
            # Being un-completed
            todo.completed_at = None

    for field, value in update_data.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)

    return todo


@router.delete("/todos/{todo_id}", status_code=204)
def delete_todo(
    lesson_id: int,
    todo_id: int,
    db: Session = Depends(get_db)
):
    """Delete a todo item."""
    get_lesson_or_404(lesson_id, db)

    todo = db.query(Todo).filter(
        Todo.id == todo_id,
        Todo.lesson_id == lesson_id
    ).first()

    if not todo:
        raise HTTPException(
            status_code=404,
            detail=f"Todo with id {todo_id} not found for lesson {lesson_id}"
        )

    db.delete(todo)
    db.commit()

    return None


# =============================================================================
# CONVENIENCE ENDPOINT: Mark Todo Complete/Incomplete
# =============================================================================
@router.patch("/todos/{todo_id}/toggle", response_model=TodoResponse)
def toggle_todo(
    lesson_id: int,
    todo_id: int,
    db: Session = Depends(get_db)
):
    """
    Toggle a todo's completion status.

    This is a convenience endpoint for quickly marking a todo as
    complete or incomplete without sending a full update body.

    If the todo is currently incomplete, it will be marked complete.
    If it's currently complete, it will be marked incomplete.
    """
    get_lesson_or_404(lesson_id, db)

    todo = db.query(Todo).filter(
        Todo.id == todo_id,
        Todo.lesson_id == lesson_id
    ).first()

    if not todo:
        raise HTTPException(
            status_code=404,
            detail=f"Todo with id {todo_id} not found for lesson {lesson_id}"
        )

    # Toggle the completion status
    todo.is_completed = not todo.is_completed

    # Update completion timestamp accordingly
    if todo.is_completed:
        todo.completed_at = datetime.utcnow()
    else:
        todo.completed_at = None

    db.commit()
    db.refresh(todo)

    return todo
