// =============================================================================
// APIService.js - Centralised API Communication
// =============================================================================
// This service handles all HTTP requests to the backend API.
//
// WHY A CENTRALISED SERVICE?
// --------------------------
// Instead of calling fetch() directly in each component, we centralise all
// API calls here. This gives us:
// 1. Consistent error handling across the app
// 2. Easy to change the base URL or add authentication headers
// 3. Single place to add loading states, retries, or caching
// 4. Easier testing - we can mock this service
//
// USAGE IN COMPONENTS:
// --------------------
// import APIService from '../services/APIService';
//
// // In an async function or useEffect:
// const data = await APIService.getWeekTimetable('2025-02-03');
// =============================================================================

// Base URL for API requests
// In development, Vite's proxy forwards /api/* to the backend
// In production, this would be configured based on deployment
const API_BASE_URL = '/api';

// =============================================================================
// Helper: Make HTTP Request
// =============================================================================
// A generic fetch wrapper that handles:
// - Adding common headers
// - Parsing JSON responses
// - Error handling
// =============================================================================
async function makeRequest(endpoint, options = {}) {
  // Build the full URL
  const url = `${API_BASE_URL}${endpoint}`;

  // Default headers for JSON APIs
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  // Merge default options with provided options
  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  // If there's a body and it's an object, stringify it
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  try {
    // Make the fetch request
    const response = await fetch(url, config);

    // Handle non-OK responses (4xx, 5xx status codes)
    if (!response.ok) {
      // Try to get error details from response body
      let errorMessage;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
      } catch {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    // Handle 204 No Content (e.g., successful DELETE)
    if (response.status === 204) {
      return null;
    }

    // Parse and return JSON response
    return await response.json();
  } catch (error) {
    // Log error for debugging
    console.error(`API Error [${options.method || 'GET'} ${endpoint}]:`, error);
    throw error;
  }
}

// =============================================================================
// API Service Object
// =============================================================================
// Exports methods for each API endpoint. Each method returns a Promise.
// =============================================================================
const APIService = {
  // ---------------------------------------------------------------------------
  // SETTINGS
  // ---------------------------------------------------------------------------

  /**
   * Get current application settings.
   * @returns {Promise<Object>} Settings object
   */
  getSettings: () => makeRequest('/settings'),

  /**
   * Update application settings.
   * @param {Object} settings - The settings to update
   * @returns {Promise<Object>} Updated settings
   */
  updateSettings: (settings) =>
    makeRequest('/settings', {
      method: 'PUT',
      body: settings,
    }),

  // ---------------------------------------------------------------------------
  // SUBJECTS
  // ---------------------------------------------------------------------------

  /**
   * Get all subjects, optionally filtered.
   * @param {Object} filters - Optional filters (academic_year, semester, is_active)
   * @returns {Promise<Array>} Array of subjects
   */
  getSubjects: (filters = {}) => {
    // Build query string from filters
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value);
      }
    });
    const queryString = params.toString();
    return makeRequest(`/subjects${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Create a new subject.
   * @param {Object} subject - The subject data
   * @returns {Promise<Object>} Created subject
   */
  createSubject: (subject) =>
    makeRequest('/subjects', {
      method: 'POST',
      body: subject,
    }),

  /**
   * Update a subject.
   * @param {number} id - Subject ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} Updated subject
   */
  updateSubject: (id, updates) =>
    makeRequest(`/subjects/${id}`, {
      method: 'PUT',
      body: updates,
    }),

  /**
   * Delete a subject.
   * @param {number} id - Subject ID
   * @returns {Promise<null>}
   */
  deleteSubject: (id) =>
    makeRequest(`/subjects/${id}`, {
      method: 'DELETE',
    }),

  // ---------------------------------------------------------------------------
  // LESSONS & TIMETABLE
  // ---------------------------------------------------------------------------

  /**
   * Get the timetable for a specific week.
   * This is the primary endpoint for the planner view.
   *
   * @param {string} startDate - The Monday of the week (YYYY-MM-DD format)
   * @returns {Promise<Object>} Week timetable with days, lessons, and Week A/B info
   *
   * @example
   * const week = await APIService.getWeekTimetable('2025-02-03');
   * console.log(week.primary_week); // "Week A" or "Week B"
   * console.log(week.days[0].lessons); // Monday's lessons
   */
  getWeekTimetable: (startDate) =>
    makeRequest(`/lessons/week?start_date=${startDate}`),

  /**
   * Get a specific lesson with all its details (notes, resources, todos).
   * @param {number} id - Lesson ID
   * @returns {Promise<Object>} Lesson with nested items
   */
  getLesson: (id) => makeRequest(`/lessons/${id}`),

  /**
   * Create a new lesson.
   * @param {Object} lesson - Lesson data (date, period, subject_id)
   * @returns {Promise<Object>} Created lesson
   */
  createLesson: (lesson) =>
    makeRequest('/lessons', {
      method: 'POST',
      body: lesson,
    }),

  /**
   * Update a lesson.
   * @param {number} id - Lesson ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} Updated lesson
   */
  updateLesson: (id, updates) =>
    makeRequest(`/lessons/${id}`, {
      method: 'PUT',
      body: updates,
    }),

  /**
   * Delete a lesson.
   * @param {number} id - Lesson ID
   * @returns {Promise<null>}
   */
  deleteLesson: (id) =>
    makeRequest(`/lessons/${id}`, {
      method: 'DELETE',
    }),

  // ---------------------------------------------------------------------------
  // NOTES (attached to lessons)
  // ---------------------------------------------------------------------------

  /**
   * Add a note to a lesson.
   * @param {number} lessonId - The lesson to attach the note to
   * @param {Object} note - Note data (title, content)
   * @returns {Promise<Object>} Created note
   */
  createNote: (lessonId, note) =>
    makeRequest(`/lessons/${lessonId}/notes`, {
      method: 'POST',
      body: note,
    }),

  /**
   * Update a note.
   * @param {number} lessonId - Parent lesson ID
   * @param {number} noteId - Note ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} Updated note
   */
  updateNote: (lessonId, noteId, updates) =>
    makeRequest(`/lessons/${lessonId}/notes/${noteId}`, {
      method: 'PUT',
      body: updates,
    }),

  /**
   * Delete a note.
   * @param {number} lessonId - Parent lesson ID
   * @param {number} noteId - Note ID
   * @returns {Promise<null>}
   */
  deleteNote: (lessonId, noteId) =>
    makeRequest(`/lessons/${lessonId}/notes/${noteId}`, {
      method: 'DELETE',
    }),

  // ---------------------------------------------------------------------------
  // RESOURCES (attached to lessons)
  // ---------------------------------------------------------------------------

  /**
   * Add a resource to a lesson.
   * @param {number} lessonId - The lesson to attach the resource to
   * @param {Object} resource - Resource data (title, url, etc.)
   * @returns {Promise<Object>} Created resource
   */
  createResource: (lessonId, resource) =>
    makeRequest(`/lessons/${lessonId}/resources`, {
      method: 'POST',
      body: resource,
    }),

  /**
   * Update a resource.
   * @param {number} lessonId - Parent lesson ID
   * @param {number} resourceId - Resource ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} Updated resource
   */
  updateResource: (lessonId, resourceId, updates) =>
    makeRequest(`/lessons/${lessonId}/resources/${resourceId}`, {
      method: 'PUT',
      body: updates,
    }),

  /**
   * Delete a resource.
   * @param {number} lessonId - Parent lesson ID
   * @param {number} resourceId - Resource ID
   * @returns {Promise<null>}
   */
  deleteResource: (lessonId, resourceId) =>
    makeRequest(`/lessons/${lessonId}/resources/${resourceId}`, {
      method: 'DELETE',
    }),

  // ---------------------------------------------------------------------------
  // TODOS (attached to lessons)
  // ---------------------------------------------------------------------------

  /**
   * Add a todo to a lesson.
   * @param {number} lessonId - The lesson to attach the todo to
   * @param {Object} todo - Todo data (content, priority, due_date)
   * @returns {Promise<Object>} Created todo
   */
  createTodo: (lessonId, todo) =>
    makeRequest(`/lessons/${lessonId}/todos`, {
      method: 'POST',
      body: todo,
    }),

  /**
   * Update a todo.
   * @param {number} lessonId - Parent lesson ID
   * @param {number} todoId - Todo ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} Updated todo
   */
  updateTodo: (lessonId, todoId, updates) =>
    makeRequest(`/lessons/${lessonId}/todos/${todoId}`, {
      method: 'PUT',
      body: updates,
    }),

  /**
   * Toggle a todo's completion status.
   * @param {number} lessonId - Parent lesson ID
   * @param {number} todoId - Todo ID
   * @returns {Promise<Object>} Updated todo
   */
  toggleTodo: (lessonId, todoId) =>
    makeRequest(`/lessons/${lessonId}/todos/${todoId}/toggle`, {
      method: 'PATCH',
    }),

  /**
   * Delete a todo.
   * @param {number} lessonId - Parent lesson ID
   * @param {number} todoId - Todo ID
   * @returns {Promise<null>}
   */
  deleteTodo: (lessonId, todoId) =>
    makeRequest(`/lessons/${lessonId}/todos/${todoId}`, {
      method: 'DELETE',
    }),
};

export default APIService;
