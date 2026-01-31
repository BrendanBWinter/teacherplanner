// =============================================================================
// LessonDetail.jsx - Lesson Detail Modal/Panel
// =============================================================================
// This component displays when a timetable slot is clicked.
// It allows viewing and editing:
// - Subject assignment
// - Notes
// - Resources
// - Todos
//
// REACT STATE UPDATE FLOW:
// ========================
// When you modify something (e.g., add a note), here's what happens:
//
// 1. USER ACTION: User types in the note form and clicks "Add Note"
//
// 2. EVENT HANDLER: The onClick calls our handleAddNote function
//
// 3. API CALL: handleAddNote calls APIService.createNote() which sends
//    the data to the backend
//
// 4. STATE UPDATE: After successful API response, we call onLessonUpdated()
//    which is a callback prop from the parent component (App.jsx)
//
// 5. PARENT UPDATES: App.jsx receives the callback and calls refreshWeekData()
//    which fetches fresh data from the API
//
// 6. STATE PROPAGATION: The new weekData flows down through props to
//    TimetableGrid, which re-renders with the updated lesson data
//
// 7. UI UPDATES: React's reconciliation process updates only the changed DOM
//
// This is the "unidirectional data flow" pattern:
// User Action → Event Handler → API Call → State Update → Props Flow Down → Re-render
// =============================================================================

import { useState } from 'react';
import './LessonDetail.css';
import APIService from '../services/APIService';

// =============================================================================
// Main LessonDetail Component
// =============================================================================
export default function LessonDetail({
  // The slot data from TimetableGrid (date, period, lesson, subject, etc.)
  slotData,
  // List of all subjects for the dropdown
  subjects,
  // Callback to close this modal
  onClose,
  // Callback when lesson is updated (parent refreshes data)
  onLessonUpdated,
}) {
  // -------------------------------------------------------------------------
  // Local State
  // -------------------------------------------------------------------------
  // We use local state for form inputs. This state is "controlled" - React
  // controls the input values via state, not the DOM.
  // -------------------------------------------------------------------------

  // Which tab is active (notes, resources, todos)
  const [activeTab, setActiveTab] = useState('notes');

  // New note form
  const [newNoteTitle, setNewNoteTitle] = useState('');
  const [newNoteContent, setNewNoteContent] = useState('');

  // New todo form
  const [newTodoContent, setNewTodoContent] = useState('');

  // New resource form
  const [newResourceTitle, setNewResourceTitle] = useState('');
  const [newResourceUrl, setNewResourceUrl] = useState('');

  // Subject selection for new/empty lessons
  const [selectedSubjectId, setSelectedSubjectId] = useState(
    slotData.lesson?.subject_id || ''
  );

  // Loading state for API calls
  const [isLoading, setIsLoading] = useState(false);

  // Error message
  const [error, setError] = useState(null);

  // -------------------------------------------------------------------------
  // Destructure slot data for easier access
  // -------------------------------------------------------------------------
  const { date, period, lesson, subject, cycleDay, weekLabel } = slotData;

  // -------------------------------------------------------------------------
  // Handler: Create or Update Lesson Subject
  // -------------------------------------------------------------------------
  // If there's no lesson for this slot, create one.
  // If there is, update its subject.
  // -------------------------------------------------------------------------
  async function handleSubjectChange(subjectId) {
    setIsLoading(true);
    setError(null);

    try {
      if (!lesson) {
        // Create new lesson
        await APIService.createLesson({
          date,
          period,
          subject_id: parseInt(subjectId),
        });
      } else {
        // Update existing lesson
        await APIService.updateLesson(lesson.id, {
          subject_id: parseInt(subjectId),
        });
      }

      // Notify parent to refresh data
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Handler: Add Note
  // -------------------------------------------------------------------------
  // HOW STATE UPDATES WORK:
  // 1. User fills form → local state (newNoteTitle, newNoteContent) updates
  // 2. User clicks Add → handleAddNote is called
  // 3. We call APIService.createNote() → backend creates the note
  // 4. On success, we call onLessonUpdated() → parent component callback
  // 5. Parent fetches fresh data → new weekData flows down via props
  // 6. React re-renders this component with the new note in lesson.notes
  // -------------------------------------------------------------------------
  async function handleAddNote() {
    if (!newNoteContent.trim()) return;
    if (!lesson) {
      setError('Please assign a subject first');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await APIService.createNote(lesson.id, {
        title: newNoteTitle || null,
        content: newNoteContent,
      });

      // Clear form
      setNewNoteTitle('');
      setNewNoteContent('');

      // Notify parent to refresh
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Handler: Delete Note
  // -------------------------------------------------------------------------
  async function handleDeleteNote(noteId) {
    setIsLoading(true);
    setError(null);

    try {
      await APIService.deleteNote(lesson.id, noteId);
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Handler: Add Todo
  // -------------------------------------------------------------------------
  async function handleAddTodo() {
    if (!newTodoContent.trim()) return;
    if (!lesson) {
      setError('Please assign a subject first');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await APIService.createTodo(lesson.id, {
        content: newTodoContent,
      });

      setNewTodoContent('');
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Handler: Toggle Todo Completion
  // -------------------------------------------------------------------------
  async function handleToggleTodo(todoId) {
    setIsLoading(true);
    setError(null);

    try {
      await APIService.toggleTodo(lesson.id, todoId);
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Handler: Delete Todo
  // -------------------------------------------------------------------------
  async function handleDeleteTodo(todoId) {
    setIsLoading(true);
    setError(null);

    try {
      await APIService.deleteTodo(lesson.id, todoId);
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Handler: Add Resource
  // -------------------------------------------------------------------------
  async function handleAddResource() {
    if (!newResourceTitle.trim()) return;
    if (!lesson) {
      setError('Please assign a subject first');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await APIService.createResource(lesson.id, {
        title: newResourceTitle,
        url: newResourceUrl || null,
        resource_type: newResourceUrl ? 'link' : 'other',
      });

      setNewResourceTitle('');
      setNewResourceUrl('');
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Handler: Delete Resource
  // -------------------------------------------------------------------------
  async function handleDeleteResource(resourceId) {
    setIsLoading(true);
    setError(null);

    try {
      await APIService.deleteResource(lesson.id, resourceId);
      onLessonUpdated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div className="lesson-detail-overlay" onClick={onClose}>
      {/* Stop click propagation so clicking inside doesn't close the modal */}
      <div className="lesson-detail-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="header-info">
            <h2>{date} - Period {period}</h2>
            <span className="week-badge">{weekLabel} (Day {cycleDay})</span>
          </div>
          <button className="close-btn" onClick={onClose}>X</button>
        </div>

        {/* Error display */}
        {error && <div className="error-message">{error}</div>}

        {/* Subject Selection */}
        <div className="subject-section">
          <label htmlFor="subject-select">Subject:</label>
          <select
            id="subject-select"
            value={selectedSubjectId}
            onChange={(e) => {
              setSelectedSubjectId(e.target.value);
              if (e.target.value) {
                handleSubjectChange(e.target.value);
              }
            }}
            disabled={isLoading}
          >
            <option value="">-- Select Subject --</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} {s.code ? `(${s.code})` : ''}
              </option>
            ))}
          </select>

          {subject && (
            <div
              className="subject-color-badge"
              style={{ backgroundColor: subject.colour || '#666' }}
            />
          )}
        </div>

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'notes' ? 'active' : ''}`}
            onClick={() => setActiveTab('notes')}
          >
            Notes ({lesson?.notes?.length || 0})
          </button>
          <button
            className={`tab ${activeTab === 'todos' ? 'active' : ''}`}
            onClick={() => setActiveTab('todos')}
          >
            Todos ({lesson?.todos?.length || 0})
          </button>
          <button
            className={`tab ${activeTab === 'resources' ? 'active' : ''}`}
            onClick={() => setActiveTab('resources')}
          >
            Resources ({lesson?.resources?.length || 0})
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {/* ---------------------------------------------------------------
              NOTES TAB
              --------------------------------------------------------------- */}
          {activeTab === 'notes' && (
            <div className="notes-section">
              {/* Add note form */}
              <div className="add-form">
                <input
                  type="text"
                  placeholder="Note title (optional)"
                  value={newNoteTitle}
                  onChange={(e) => setNewNoteTitle(e.target.value)}
                  disabled={isLoading}
                />
                <textarea
                  placeholder="Note content..."
                  value={newNoteContent}
                  onChange={(e) => setNewNoteContent(e.target.value)}
                  disabled={isLoading}
                  rows={3}
                />
                <button
                  className="add-btn"
                  onClick={handleAddNote}
                  disabled={isLoading || !newNoteContent.trim()}
                >
                  Add Note
                </button>
              </div>

              {/* Notes list */}
              <div className="items-list">
                {lesson?.notes?.length > 0 ? (
                  lesson.notes.map((note) => (
                    <div key={note.id} className="item-card">
                      {note.title && <div className="item-title">{note.title}</div>}
                      <div className="item-content">{note.content}</div>
                      <button
                        className="delete-btn"
                        onClick={() => handleDeleteNote(note.id)}
                        disabled={isLoading}
                      >
                        Delete
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="empty-message">No notes yet</p>
                )}
              </div>
            </div>
          )}

          {/* ---------------------------------------------------------------
              TODOS TAB
              --------------------------------------------------------------- */}
          {activeTab === 'todos' && (
            <div className="todos-section">
              {/* Add todo form */}
              <div className="add-form inline">
                <input
                  type="text"
                  placeholder="New todo..."
                  value={newTodoContent}
                  onChange={(e) => setNewTodoContent(e.target.value)}
                  disabled={isLoading}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTodo()}
                />
                <button
                  className="add-btn"
                  onClick={handleAddTodo}
                  disabled={isLoading || !newTodoContent.trim()}
                >
                  Add
                </button>
              </div>

              {/* Todos list */}
              <div className="items-list">
                {lesson?.todos?.length > 0 ? (
                  lesson.todos.map((todo) => (
                    <div
                      key={todo.id}
                      className={`item-card todo ${todo.is_completed ? 'completed' : ''}`}
                    >
                      <label className="todo-checkbox">
                        <input
                          type="checkbox"
                          checked={todo.is_completed}
                          onChange={() => handleToggleTodo(todo.id)}
                          disabled={isLoading}
                        />
                        <span className="todo-content">{todo.content}</span>
                      </label>
                      <button
                        className="delete-btn"
                        onClick={() => handleDeleteTodo(todo.id)}
                        disabled={isLoading}
                      >
                        Delete
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="empty-message">No todos yet</p>
                )}
              </div>
            </div>
          )}

          {/* ---------------------------------------------------------------
              RESOURCES TAB
              --------------------------------------------------------------- */}
          {activeTab === 'resources' && (
            <div className="resources-section">
              {/* Add resource form */}
              <div className="add-form">
                <input
                  type="text"
                  placeholder="Resource title"
                  value={newResourceTitle}
                  onChange={(e) => setNewResourceTitle(e.target.value)}
                  disabled={isLoading}
                />
                <input
                  type="url"
                  placeholder="URL (optional)"
                  value={newResourceUrl}
                  onChange={(e) => setNewResourceUrl(e.target.value)}
                  disabled={isLoading}
                />
                <button
                  className="add-btn"
                  onClick={handleAddResource}
                  disabled={isLoading || !newResourceTitle.trim()}
                >
                  Add Resource
                </button>
              </div>

              {/* Resources list */}
              <div className="items-list">
                {lesson?.resources?.length > 0 ? (
                  lesson.resources.map((resource) => (
                    <div key={resource.id} className="item-card resource">
                      <div className="item-title">{resource.title}</div>
                      {resource.url && (
                        <a
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="resource-link"
                        >
                          {resource.url}
                        </a>
                      )}
                      <button
                        className="delete-btn"
                        onClick={() => handleDeleteResource(resource.id)}
                        disabled={isLoading}
                      >
                        Delete
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="empty-message">No resources yet</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Loading indicator */}
        {isLoading && <div className="loading-overlay">Saving...</div>}
      </div>
    </div>
  );
}
