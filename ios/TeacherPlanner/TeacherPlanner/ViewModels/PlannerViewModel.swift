// =============================================================================
// PlannerViewModel.swift - Main View Model for Teacher Planner
// =============================================================================
// This ViewModel manages the app's state and business logic.
// It uses ObservableObject to notify SwiftUI views when data changes.
//
// =============================================================================
// OBSERVABLEOBJECT EXPLAINED
// =============================================================================
//
// ObservableObject is a protocol that makes a class observable by SwiftUI.
// When properties marked with @Published change, SwiftUI automatically
// re-renders any views that depend on those properties.
//
// THE FLOW:
// ---------
// 1. View observes ViewModel via @StateObject or @ObservedObject
// 2. ViewModel has @Published properties (e.g., weekData, todos)
// 3. User action triggers a method (e.g., toggleTodo)
// 4. Method updates a @Published property
// 5. SwiftUI detects the change and re-renders affected views
//
// VISUAL REPRESENTATION:
// ----------------------
//
//   ┌─────────────────────────────────────────────────────────────────────┐
//   │                     PlannerViewModel                                │
//   │                  (ObservableObject)                                 │
//   │                                                                     │
//   │   @Published var weekData: WeekTimetable?  ◄──── Changes here      │
//   │   @Published var selectedLesson: Lesson?        trigger UI          │
//   │   @Published var subjects: [Subject]            updates             │
//   │   @Published var isLoading: Bool                                    │
//   │                                                                     │
//   └─────────────────────────────────────────────────────────────────────┘
//                              │
//                              │  Views observe via @StateObject
//                              │
//                              ▼
//   ┌─────────────────────────────────────────────────────────────────────┐
//   │                         SwiftUI Views                               │
//   │                                                                     │
//   │   SidebarView ───────────────────────────────────────────┐          │
//   │   LessonDetailView ──────────────────────────────────────┤          │
//   │   TodayView ─────────────────────────────────────────────┤          │
//   │                                                          │          │
//   │   All automatically re-render when @Published changes! ──┘          │
//   │                                                                     │
//   └─────────────────────────────────────────────────────────────────────┘
//
// EXAMPLE - TOGGLING A TODO:
// --------------------------
// 1. User taps checkbox on a Todo item
// 2. View calls: viewModel.toggleTodo(todo)
// 3. toggleTodo() calls API to update backend
// 4. On success, toggleTodo() calls refreshSelectedLesson()
// 5. refreshSelectedLesson() fetches fresh data and updates @Published selectedLesson
// 6. SwiftUI sees selectedLesson changed → re-renders LessonDetailView
// 7. The checkbox now shows the new state!
//
// WHY @MainActor?
// ---------------
// UI updates must happen on the main thread. @MainActor ensures all
// property updates and method calls happen on the main thread automatically.
// =============================================================================

import Foundation
import SwiftUI

// =============================================================================
// Navigation State
// =============================================================================
// Enum to track what's selected in the sidebar

enum SidebarItem: Hashable {
    case today
    case thisWeek
    case subjects
    case subject(Subject)
}

// =============================================================================
// PlannerViewModel
// =============================================================================

@MainActor  // Ensures all updates happen on main thread (required for UI)
class PlannerViewModel: ObservableObject {
    // -------------------------------------------------------------------------
    // MARK: - Published Properties
    // -------------------------------------------------------------------------
    // @Published marks properties that, when changed, notify observers.
    // SwiftUI views that use @StateObject or @ObservedObject will automatically
    // re-render when these properties change.
    // -------------------------------------------------------------------------

    /// Current week's timetable data
    @Published var weekData: WeekTimetable?

    /// All active subjects
    @Published var subjects: [Subject] = []

    /// App settings (periods per day, etc.)
    @Published var settings: Settings?

    /// Currently selected lesson (for detail view)
    @Published var selectedLesson: Lesson?

    /// Currently selected sidebar item
    @Published var selectedSidebarItem: SidebarItem? = .today

    /// Loading state
    @Published var isLoading: Bool = false

    /// Error message to display
    @Published var errorMessage: String?

    /// Today's date string (YYYY-MM-DD)
    @Published var todayDateString: String

    /// Current week start date (Monday)
    @Published var currentWeekStart: String

    // -------------------------------------------------------------------------
    // MARK: - Private Properties
    // -------------------------------------------------------------------------

    private let apiService = APIService.shared
    private let dateFormatter: DateFormatter

    // -------------------------------------------------------------------------
    // MARK: - Initialization
    // -------------------------------------------------------------------------

    init() {
        // Set up date formatter
        self.dateFormatter = DateFormatter()
        self.dateFormatter.dateFormat = "yyyy-MM-dd"

        // Calculate today's date
        let today = Date()
        self.todayDateString = dateFormatter.string(from: today)

        // Calculate Monday of current week
        let calendar = Calendar.current
        let weekday = calendar.component(.weekday, from: today)
        // Sunday = 1, Monday = 2, ..., Saturday = 7
        // We want to go back to Monday
        let daysToSubtract = (weekday == 1) ? 6 : (weekday - 2)
        let monday = calendar.date(byAdding: .day, value: -daysToSubtract, to: today)!
        self.currentWeekStart = dateFormatter.string(from: monday)
    }

    // -------------------------------------------------------------------------
    // MARK: - Data Loading
    // -------------------------------------------------------------------------

    /// Load all initial data (settings, subjects, week timetable)
    func loadInitialData() async {
        isLoading = true
        errorMessage = nil

        do {
            // Load in parallel using async let
            async let settingsTask = apiService.getSettings()
            async let subjectsTask = apiService.getSubjects(isActive: true)
            async let weekTask = apiService.getWeekTimetable(startDate: currentWeekStart)

            // Wait for all to complete
            let (loadedSettings, loadedSubjects, loadedWeek) = try await (
                settingsTask,
                subjectsTask,
                weekTask
            )

            // Update published properties (triggers UI update)
            self.settings = loadedSettings
            self.subjects = loadedSubjects
            self.weekData = loadedWeek

        } catch {
            self.errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    /// Refresh the current week's data
    func refreshWeekData() async {
        do {
            let week = try await apiService.getWeekTimetable(startDate: currentWeekStart)
            self.weekData = week
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// Navigate to previous week
    func goToPreviousWeek() async {
        guard let current = dateFormatter.date(from: currentWeekStart) else { return }
        let previous = Calendar.current.date(byAdding: .day, value: -7, to: current)!
        currentWeekStart = dateFormatter.string(from: previous)
        await refreshWeekData()
    }

    /// Navigate to next week
    func goToNextWeek() async {
        guard let current = dateFormatter.date(from: currentWeekStart) else { return }
        let next = Calendar.current.date(byAdding: .day, value: 7, to: current)!
        currentWeekStart = dateFormatter.string(from: next)
        await refreshWeekData()
    }

    /// Go to current week
    func goToCurrentWeek() async {
        let today = Date()
        let calendar = Calendar.current
        let weekday = calendar.component(.weekday, from: today)
        let daysToSubtract = (weekday == 1) ? 6 : (weekday - 2)
        let monday = calendar.date(byAdding: .day, value: -daysToSubtract, to: today)!
        currentWeekStart = dateFormatter.string(from: monday)
        await refreshWeekData()
    }

    // -------------------------------------------------------------------------
    // MARK: - Lesson Selection
    // -------------------------------------------------------------------------

    /// Select a lesson and load its full details
    func selectLesson(_ lesson: Lesson) async {
        do {
            // Fetch full lesson details (includes notes, resources, todos)
            let fullLesson = try await apiService.getLesson(id: lesson.id)
            self.selectedLesson = fullLesson
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// Refresh the currently selected lesson
    func refreshSelectedLesson() async {
        guard let lesson = selectedLesson else { return }
        await selectLesson(lesson)
    }

    /// Clear the selected lesson
    func clearSelectedLesson() {
        selectedLesson = nil
    }

    // -------------------------------------------------------------------------
    // MARK: - Todo Operations
    // -------------------------------------------------------------------------

    /// Toggle a todo's completion status
    ///
    /// THIS IS THE KEY EXAMPLE OF ObservableObject IN ACTION:
    ///
    /// 1. User taps the checkbox next to a todo
    /// 2. View calls viewModel.toggleTodo(todo)
    /// 3. We call the API to toggle on the backend
    /// 4. We refresh the selected lesson to get updated data
    /// 5. Setting self.selectedLesson triggers @Published
    /// 6. SwiftUI detects the change and re-renders LessonDetailView
    /// 7. The checkbox now shows the new completed state!
    ///
    func toggleTodo(_ todo: Todo) async {
        guard let lesson = selectedLesson else { return }

        do {
            // Call API to toggle the todo
            _ = try await apiService.toggleTodo(
                lessonId: lesson.id,
                todoId: todo.id
            )

            // Refresh the lesson to get updated todo state
            // This updates @Published selectedLesson, triggering UI refresh
            await refreshSelectedLesson()

            // Also refresh week data so the indicators update
            await refreshWeekData()

        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// Add a new todo to the current lesson
    func addTodo(content: String) async {
        guard let lesson = selectedLesson else { return }

        do {
            _ = try await apiService.createTodo(
                lessonId: lesson.id,
                todo: CreateTodoRequest(content: content, priority: nil, dueDate: nil)
            )
            await refreshSelectedLesson()
            await refreshWeekData()
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// Delete a todo
    func deleteTodo(_ todo: Todo) async {
        guard let lesson = selectedLesson else { return }

        do {
            try await apiService.deleteTodo(lessonId: lesson.id, todoId: todo.id)
            await refreshSelectedLesson()
            await refreshWeekData()
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    // -------------------------------------------------------------------------
    // MARK: - Note Operations
    // -------------------------------------------------------------------------

    /// Add a new note to the current lesson
    func addNote(title: String?, content: String) async {
        guard let lesson = selectedLesson else { return }

        do {
            _ = try await apiService.createNote(
                lessonId: lesson.id,
                note: CreateNoteRequest(title: title, content: content)
            )
            await refreshSelectedLesson()
            await refreshWeekData()
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// Delete a note
    func deleteNote(_ note: Note) async {
        guard let lesson = selectedLesson else { return }

        do {
            try await apiService.deleteNote(lessonId: lesson.id, noteId: note.id)
            await refreshSelectedLesson()
            await refreshWeekData()
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    // -------------------------------------------------------------------------
    // MARK: - Resource Operations
    // -------------------------------------------------------------------------

    /// Add a new resource to the current lesson
    func addResource(title: String, url: String?) async {
        guard let lesson = selectedLesson else { return }

        do {
            _ = try await apiService.createResource(
                lessonId: lesson.id,
                resource: CreateResourceRequest(
                    title: title,
                    url: url,
                    resourceType: url != nil ? "link" : nil
                )
            )
            await refreshSelectedLesson()
            await refreshWeekData()
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    /// Delete a resource
    func deleteResource(_ resource: Resource) async {
        guard let lesson = selectedLesson else { return }

        do {
            try await apiService.deleteResource(lessonId: lesson.id, resourceId: resource.id)
            await refreshSelectedLesson()
            await refreshWeekData()
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    // -------------------------------------------------------------------------
    // MARK: - Helper Methods
    // -------------------------------------------------------------------------

    /// Get today's lessons from the week data
    func getTodayLessons() -> [Lesson] {
        guard let weekData = weekData else { return [] }
        guard let today = weekData.days.first(where: { $0.date == todayDateString }) else {
            return []
        }
        return today.lessons.sorted { $0.period < $1.period }
    }

    /// Get a subject by ID
    func getSubject(id: Int) -> Subject? {
        return subjects.first { $0.id == id }
    }

    /// Get lessons for a specific subject
    func getLessonsForSubject(_ subject: Subject) -> [Lesson] {
        guard let weekData = weekData else { return [] }
        return weekData.days.flatMap { day in
            day.lessons.filter { $0.subjectId == subject.id }
        }.sorted { $0.date < $1.date || ($0.date == $1.date && $0.period < $1.period) }
    }
}
