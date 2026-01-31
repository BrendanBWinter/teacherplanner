# Teacher Planner - Project Context

A self-hosted teacher planner application designed for use in Victoria, Australia, featuring a web frontend and native iOS client for iPad use during and after classes.

---

## Project Structure

This is a **monorepo** containing three main components:

```
/
├── backend/          # FastAPI REST API server
├── frontend/         # React web application
├── ios/              # Native SwiftUI iPad app
├── docker-compose.yml
└── PROJECT_CONTEXT.md
```

---

## Architecture Overview

### Backend (`/backend`)

**Technology:** FastAPI with SQLite

The backend serves as the central API for both the web frontend and iOS app.

#### Core Features

1. **10-Working-Day Timetable Cycle (Week A/B)**
   - Support for a fortnightly timetable rotation common in Victorian schools
   - Days are numbered 1-10 across two weeks (Week A: Days 1-5, Week B: Days 6-10)
   - Mapping of calendar dates to cycle days with handling for public holidays and pupil-free days

2. **Customizable Periods/Divisions**
   - Configurable number of periods per day (e.g., 6 periods, or custom divisions)
   - Support for varying period structures (e.g., different schedules on different days)
   - Period timing metadata (start/end times) for reference

3. **Period-Attached Data**
   - **Resources:** Links, files, or references attached to specific periods
   - **Notes:** Lesson notes, observations, or reflections for each period
   - **To-Dos:** Actionable items linked to specific periods (e.g., "return marked essays")

4. **Subject Management**
   - Define subjects taught in a given semester or year
   - Associate subjects with specific periods in the timetable cycle
   - Store subject metadata (year level, class name, curriculum links)

#### Database Schema Concepts

- `CycleDay` - Represents days 1-10 in the timetable cycle
- `Period` - Time divisions within each day
- `Subject` - Subjects being taught
- `TimetableEntry` - Links subjects to specific cycle days and periods
- `Resource`, `Note`, `Todo` - Attachable items linked to timetable entries
- `CalendarMapping` - Maps real calendar dates to cycle days

---

### Frontend (`/frontend`)

**Technology:** React with Vite

A desktop-optimised web interface for planning and administration tasks.

#### Core Features

- Full timetable view showing Week A/B cycle
- Subject and period configuration interface
- Resource, note, and to-do management
- Calendar view with cycle day mapping
- Responsive but **desktop-first** design

#### Key Considerations

- Optimised for larger screens (planning at a desk)
- Keyboard shortcuts for efficient navigation
- Bulk editing capabilities for term planning

---

### iOS App (`/ios`)

**Technology:** Native SwiftUI

The **primary client** for day-to-day use on iPad during and after classes.

#### Core Features

- All capabilities from the backend (full feature parity)
- Quick access to "today's" periods and associated data
- Easy note-taking during or after lessons
- To-do management with completion tracking
- Resource viewing and linking

#### Key Considerations

- Optimised for iPad (primary device)
- Touch-friendly interface for classroom use
- Offline capability considerations (future enhancement)
- Quick-entry workflows for notes and to-dos during busy teaching periods

---

## Deployment

**Target Platform:** Unraid server via Docker Compose

```yaml
# docker-compose.yml structure (conceptual)
services:
  backend:
    # FastAPI application
    # Exposes REST API
    # SQLite database persisted via volume

  frontend:
    # React app served via nginx (or similar)
    # Configured to communicate with backend API
```

#### Deployment Notes

- SQLite database stored in a persistent Docker volume
- Frontend served as static files (production build)
- Backend handles API requests and database operations
- iOS app connects directly to the backend API over local network

---

## Development Guidelines

### Code Comments

> **Important:** This project is a learning exercise. All code should be **generously commented** to explain:
> - What the code does
> - Why specific approaches were chosen
> - How different components interact
> - Any Victorian education system-specific logic

### Coding Standards

- Clear, descriptive variable and function names
- Logical file and folder organisation
- Consistent formatting within each technology stack
- Documentation of API endpoints and data structures

---

## Victorian Education Context

This planner is designed with the Victorian (Australia) school system in mind:

- **Timetable Cycle:** Many Victorian secondary schools use a 10-day (fortnightly) timetable rotation
- **Terms:** Four terms per year with specific holiday periods
- **Curriculum:** Alignment with Victorian Curriculum where relevant
- **Reporting Periods:** Typically mid-year and end-of-year reports

---

## Future Considerations

- Offline support for iOS app
- Sync conflict resolution
- Curriculum outcome tracking
- Student list integration (optional, privacy-conscious)
- Export functionality for reports and planning documents
