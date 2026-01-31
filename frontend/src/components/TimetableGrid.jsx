// =============================================================================
// TimetableGrid.jsx - Main Timetable Display Component
// =============================================================================
// This component displays a 5-day week (Mon-Fri) with configurable periods.
// Each cell (slot) shows the subject assigned to that time slot.
//
// COMPONENT STRUCTURE:
// --------------------
// TimetableGrid
// ├── Header row (day names with Week A/B and cycle day info)
// └── Period rows
//     └── TimetableSlot (one per day per period)
//
// PROPS:
// ------
// - weekData: The week timetable data from API (includes days, lessons, etc.)
// - periodsPerDay: Number of periods (rows) to display
// - onSlotClick: Callback when a slot is clicked (opens detail view)
// - subjects: List of all subjects (for displaying subject info)
//
// REACT CONCEPTS USED:
// --------------------
// - Props: Data passed down from parent component
// - Array.map(): Transform arrays into JSX elements
// - Conditional rendering: Show different content based on state
// =============================================================================

import './TimetableGrid.css';

// =============================================================================
// TimetableSlot Component
// =============================================================================
// Represents a single cell in the timetable grid.
// Shows the subject name and indicators for notes/todos if present.
// =============================================================================
function TimetableSlot({ lesson, subject, onClick }) {
  // Determine if this slot has any content
  const hasLesson = !!lesson;
  const hasNotes = lesson?.notes?.length > 0;
  const hasTodos = lesson?.todos?.length > 0;
  const hasResources = lesson?.resources?.length > 0;

  // Count incomplete todos
  const incompleteTodos = lesson?.todos?.filter(t => !t.is_completed).length || 0;

  return (
    <div
      className={`timetable-slot ${hasLesson ? 'has-lesson' : 'empty'}`}
      onClick={onClick}
      // Apply subject colour as background if available
      style={subject?.colour ? { borderLeftColor: subject.colour } : {}}
    >
      {hasLesson ? (
        <>
          {/* Subject name or code */}
          <div className="slot-subject">
            {subject?.code || subject?.name || 'Unknown Subject'}
          </div>

          {/* Lesson title if set */}
          {lesson.title && (
            <div className="slot-title">{lesson.title}</div>
          )}

          {/* Indicators for attached items */}
          <div className="slot-indicators">
            {hasNotes && (
              <span className="indicator notes" title={`${lesson.notes.length} note(s)`}>
                {lesson.notes.length}
              </span>
            )}
            {hasTodos && (
              <span
                className={`indicator todos ${incompleteTodos > 0 ? 'has-incomplete' : ''}`}
                title={`${incompleteTodos} todo(s) remaining`}
              >
                {incompleteTodos > 0 ? incompleteTodos : ''}
              </span>
            )}
            {hasResources && (
              <span className="indicator resources" title={`${lesson.resources.length} resource(s)`}>
                {lesson.resources.length}
              </span>
            )}
          </div>
        </>
      ) : (
        // Empty slot - show plus icon to indicate it's clickable
        <div className="slot-empty">+</div>
      )}
    </div>
  );
}

// =============================================================================
// TimetableGrid Main Component
// =============================================================================
export default function TimetableGrid({
  weekData,
  periodsPerDay = 6,
  onSlotClick,
  subjects = [],
}) {
  // -------------------------------------------------------------------------
  // Early return if no data
  // -------------------------------------------------------------------------
  if (!weekData || !weekData.days) {
    return (
      <div className="timetable-loading">
        Loading timetable...
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Helper: Find subject by ID
  // -------------------------------------------------------------------------
  // Creates a lookup map for efficient subject retrieval
  const subjectMap = subjects.reduce((map, subject) => {
    map[subject.id] = subject;
    return map;
  }, {});

  // -------------------------------------------------------------------------
  // Helper: Find lesson for a specific day and period
  // -------------------------------------------------------------------------
  // Given a day's lessons array and a period number, find the matching lesson
  const findLesson = (dayLessons, period) => {
    return dayLessons.find(lesson => lesson.period === period);
  };

  // -------------------------------------------------------------------------
  // Generate period numbers array
  // -------------------------------------------------------------------------
  // Creates [1, 2, 3, 4, 5, 6] for 6 periods
  const periods = Array.from({ length: periodsPerDay }, (_, i) => i + 1);

  return (
    <div className="timetable-container">
      {/* -------------------------------------------------------------------
          HEADER: Week info and navigation
          ------------------------------------------------------------------- */}
      <div className="timetable-header">
        <h2>
          Week of {weekData.week_start} - {weekData.primary_week}
        </h2>
      </div>

      {/* -------------------------------------------------------------------
          GRID: The actual timetable
          ------------------------------------------------------------------- */}
      <div className="timetable-grid">
        {/* -----------------------------------------------------------------
            HEADER ROW: Day names
            ----------------------------------------------------------------- */}
        <div className="grid-header">
          {/* Empty cell for period column */}
          <div className="period-label header">Period</div>

          {/* Day headers */}
          {weekData.days.map((day) => (
            <div key={day.date} className="day-header">
              <div className="day-name">{day.weekday_name}</div>
              <div className="day-date">{day.date}</div>
              <div className={`day-cycle ${day.is_week_a ? 'week-a' : 'week-b'}`}>
                Day {day.cycle_day}
              </div>
            </div>
          ))}
        </div>

        {/* -----------------------------------------------------------------
            PERIOD ROWS: One row per period
            ----------------------------------------------------------------- */}
        {periods.map((period) => (
          <div key={period} className="grid-row">
            {/* Period number label */}
            <div className="period-label">
              Period {period}
            </div>

            {/* Slots for each day */}
            {weekData.days.map((day) => {
              // Find the lesson for this day and period
              const lesson = findLesson(day.lessons, period);
              // Get the subject details if there's a lesson
              const subject = lesson ? subjectMap[lesson.subject_id] : null;

              return (
                <TimetableSlot
                  key={`${day.date}-${period}`}
                  lesson={lesson}
                  subject={subject}
                  onClick={() => onSlotClick({
                    date: day.date,
                    period,
                    lesson,
                    subject,
                    cycleDay: day.cycle_day,
                    weekLabel: day.week_label,
                  })}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
