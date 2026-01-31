// =============================================================================
// App.jsx - Main Application Component
// =============================================================================
// This is the root component that orchestrates the entire application.
// It manages the global state and renders child components.
//
// =============================================================================
// REACT STATE MANAGEMENT EXPLAINED
// =============================================================================
//
// React uses a "unidirectional data flow" pattern:
//
//   ┌─────────────────────────────────────────────────────────────────────┐
//   │                         STATE LIVES HERE                            │
//   │                           (App.jsx)                                 │
//   │                                                                     │
//   │   weekData ─────────────────────────────────────────────────┐      │
//   │   subjects ─────────────────────────────────────────────────┤      │
//   │   settings ─────────────────────────────────────────────────┤      │
//   │                                                             │      │
//   └─────────────────────────────────────────────────────────────│──────┘
//                                                                 │
//                              PROPS FLOW DOWN                    │
//                                    │                            │
//                                    ▼                            │
//   ┌─────────────────────────────────────────────────────────────│──────┐
//   │                       TimetableGrid                         │      │
//   │                                                             │      │
//   │   Receives: weekData, subjects, onSlotClick                 │      │
//   │   Renders the grid, calls onSlotClick when slot clicked     │      │
//   │                                                             │      │
//   └─────────────────────────────────────────────────────────────│──────┘
//                                                                 │
//                                    │                            │
//                                    ▼                            │
//   ┌─────────────────────────────────────────────────────────────│──────┐
//   │                       LessonDetail                          │      │
//   │                                                             │      │
//   │   Receives: slotData, subjects, onClose, onLessonUpdated    │      │
//   │   User makes changes → API call → onLessonUpdated()  ───────┘      │
//   │                                                                     │
//   └─────────────────────────────────────────────────────────────────────┘
//                                    │
//                                    │ CALLBACKS FLOW UP
//                                    ▼
//   ┌─────────────────────────────────────────────────────────────────────┐
//   │   App.jsx receives callback                                         │
//   │   → Calls refreshWeekData()                                         │
//   │   → API fetches fresh data                                          │
//   │   → setWeekData(newData) updates state                              │
//   │   → React re-renders with new data                                  │
//   └─────────────────────────────────────────────────────────────────────┘
//
// KEY CONCEPTS:
// -------------
// 1. STATE: Variables that, when changed, cause React to re-render
//    - Created with useState() hook
//    - Updated with the setter function (e.g., setWeekData)
//
// 2. PROPS: Data passed from parent to child components
//    - Read-only in the child component
//    - Changes when parent re-renders with new values
//
// 3. EFFECTS: Side effects like API calls
//    - Created with useEffect() hook
//    - Runs after render, based on dependencies
//
// 4. CALLBACKS: Functions passed down as props
//    - Allow children to communicate back to parents
//    - Parent defines the function, child calls it
// =============================================================================

import { useState, useEffect } from 'react';
import './App.css';

// Import components
import TimetableGrid from './components/TimetableGrid';
import LessonDetail from './components/LessonDetail';

// Import API service
import APIService from './services/APIService';

// =============================================================================
// Helper: Get Monday of a given week
// =============================================================================
function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  // Adjust: Sunday (0) becomes -6, other days become positive offset
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  return d.toISOString().split('T')[0]; // Format: YYYY-MM-DD
}

// =============================================================================
// Main App Component
// =============================================================================
export default function App() {
  // ---------------------------------------------------------------------------
  // STATE DECLARATIONS
  // ---------------------------------------------------------------------------
  // useState returns [currentValue, setterFunction]
  // When we call the setter, React schedules a re-render
  // ---------------------------------------------------------------------------

  // The current week being displayed (YYYY-MM-DD format, should be a Monday)
  const [currentWeekStart, setCurrentWeekStart] = useState(() => getMonday(new Date()));

  // Week timetable data from the API
  // This is the main data that TimetableGrid displays
  const [weekData, setWeekData] = useState(null);

  // All subjects (for dropdown and display)
  const [subjects, setSubjects] = useState([]);

  // App settings (periods per day, etc.)
  const [settings, setSettings] = useState(null);

  // Currently selected slot (when clicking a timetable cell)
  // When this is set, the LessonDetail modal opens
  const [selectedSlot, setSelectedSlot] = useState(null);

  // Loading and error states for better UX
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // ---------------------------------------------------------------------------
  // EFFECT: Load initial data on mount
  // ---------------------------------------------------------------------------
  // useEffect with empty dependency array [] runs once when component mounts.
  // It's like componentDidMount in class components.
  // ---------------------------------------------------------------------------
  useEffect(() => {
    loadInitialData();
  }, []);

  // ---------------------------------------------------------------------------
  // EFFECT: Reload week data when currentWeekStart changes
  // ---------------------------------------------------------------------------
  // When we navigate to a different week, this effect runs and fetches
  // the new week's data.
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (currentWeekStart) {
      loadWeekData();
    }
  }, [currentWeekStart]);

  // ---------------------------------------------------------------------------
  // Data Loading Functions
  // ---------------------------------------------------------------------------

  async function loadInitialData() {
    setIsLoading(true);
    setError(null);

    try {
      // Load settings and subjects in parallel
      const [settingsData, subjectsData] = await Promise.all([
        APIService.getSettings(),
        APIService.getSubjects({ is_active: true }),
      ]);

      setSettings(settingsData);
      setSubjects(subjectsData);

      // Load week data (this also runs via useEffect, but we do it here too
      // to avoid a flash of empty content)
      await loadWeekData();
    } catch (err) {
      setError('Failed to load initial data: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadWeekData() {
    try {
      const data = await APIService.getWeekTimetable(currentWeekStart);
      setWeekData(data);
    } catch (err) {
      // Don't set main error - just log it
      console.error('Failed to load week data:', err);
    }
  }

  // ---------------------------------------------------------------------------
  // Event Handlers
  // ---------------------------------------------------------------------------

  // Navigate to previous week
  function handlePrevWeek() {
    const current = new Date(currentWeekStart);
    current.setDate(current.getDate() - 7);
    setCurrentWeekStart(current.toISOString().split('T')[0]);
  }

  // Navigate to next week
  function handleNextWeek() {
    const current = new Date(currentWeekStart);
    current.setDate(current.getDate() + 7);
    setCurrentWeekStart(current.toISOString().split('T')[0]);
  }

  // Navigate to current week
  function handleToday() {
    setCurrentWeekStart(getMonday(new Date()));
  }

  // Handle slot click - opens the detail modal
  function handleSlotClick(slotData) {
    setSelectedSlot(slotData);
  }

  // Close the detail modal
  function handleCloseDetail() {
    setSelectedSlot(null);
  }

  // ---------------------------------------------------------------------------
  // Callback: When a lesson is updated in LessonDetail
  // ---------------------------------------------------------------------------
  // This is the KEY callback that demonstrates React's state update flow:
  //
  // 1. User edits something in LessonDetail (e.g., adds a note)
  // 2. LessonDetail calls APIService to save to backend
  // 3. After success, LessonDetail calls this callback (onLessonUpdated)
  // 4. We call loadWeekData() to fetch fresh data from the API
  // 5. setWeekData(newData) updates state
  // 6. React re-renders App, which re-renders TimetableGrid with new data
  // 7. The grid now shows the updated lesson with the new note
  //
  // This ensures the UI always reflects the server's state (single source of truth).
  // ---------------------------------------------------------------------------
  async function handleLessonUpdated() {
    // Refresh the week data to get the updated lesson
    await loadWeekData();

    // Also refresh the selected slot data if it's still open
    // We need to find the updated lesson in the new week data
    if (selectedSlot && weekData) {
      const day = weekData.days.find(d => d.date === selectedSlot.date);
      if (day) {
        const updatedLesson = day.lessons.find(l => l.period === selectedSlot.period);
        const subject = updatedLesson ? subjects.find(s => s.id === updatedLesson.subject_id) : null;

        setSelectedSlot({
          ...selectedSlot,
          lesson: updatedLesson || null,
          subject: subject || null,
        });
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>Teacher Planner</h1>
        <p>Victoria, Australia</p>
      </header>

      {/* Main content */}
      <main className="app-main">
        {/* Error display */}
        {error && (
          <div className="app-error">
            {error}
            <button onClick={loadInitialData}>Retry</button>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="app-loading">Loading...</div>
        )}

        {/* Week navigation */}
        {!isLoading && !error && (
          <>
            <div className="week-navigation">
              <button onClick={handlePrevWeek}>&larr; Previous Week</button>
              <button onClick={handleToday}>Today</button>
              <button onClick={handleNextWeek}>Next Week &rarr;</button>
            </div>

            {/* Timetable Grid */}
            <TimetableGrid
              weekData={weekData}
              periodsPerDay={settings?.periods_per_day || 6}
              onSlotClick={handleSlotClick}
              subjects={subjects}
            />
          </>
        )}

        {/* Lesson Detail Modal */}
        {selectedSlot && (
          <LessonDetail
            slotData={selectedSlot}
            subjects={subjects}
            onClose={handleCloseDetail}
            onLessonUpdated={handleLessonUpdated}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          {settings?.periods_per_day || 6} periods per day |
          {weekData?.primary_week || 'Loading...'} |
          Cycle: {settings?.cycle_length || 10} days
        </p>
      </footer>
    </div>
  );
}
