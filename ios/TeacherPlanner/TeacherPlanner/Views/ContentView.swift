// =============================================================================
// ContentView.swift - Main App View with NavigationSplitView
// =============================================================================
// This is the root view of the app, using NavigationSplitView for iPad.
//
// NAVIGATIONSPLITVIEW EXPLAINED:
// ------------------------------
// NavigationSplitView creates a multi-column layout ideal for iPad:
// - Sidebar (left): Navigation options (Today, This Week, Subjects)
// - Content (middle): List of items based on selection
// - Detail (right): Detailed view of selected item
//
// On iPhone, it collapses to a single-column navigation stack.
//
// STATEOBJECT vs OBSERVEDOBJECT:
// ------------------------------
// - @StateObject: Use when THIS view OWNS the object (creates it)
// - @ObservedObject: Use when the object is PASSED IN from parent
//
// Here we use @StateObject because ContentView creates and owns the ViewModel.
// Child views will use @ObservedObject since they receive it from parent.
// =============================================================================

import SwiftUI

struct ContentView: View {
    // -------------------------------------------------------------------------
    // @StateObject: This view OWNS the ViewModel
    // -------------------------------------------------------------------------
    // @StateObject ensures the ViewModel is created once and persists across
    // view re-renders. It's like @State but for reference types (classes).
    // -------------------------------------------------------------------------
    @StateObject private var viewModel = PlannerViewModel()

    var body: some View {
        // ---------------------------------------------------------------------
        // NavigationSplitView: Three-column layout for iPad
        // ---------------------------------------------------------------------
        // - sidebar: Left column with navigation options
        // - content: Middle column (optional, we use two-column here)
        // - detail: Right column with detail view
        //
        // For a two-column layout, we omit the middle 'content' column.
        // ---------------------------------------------------------------------
        NavigationSplitView {
            // SIDEBAR
            SidebarView(viewModel: viewModel)
        } detail: {
            // DETAIL VIEW
            // Shows content based on sidebar selection
            DetailContentView(viewModel: viewModel)
        }
        // Load data when view appears
        .task {
            await viewModel.loadInitialData()
        }
        // Show error alerts
        .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
            Button("OK") {
                viewModel.errorMessage = nil
            }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }
}

// =============================================================================
// SidebarView - Navigation Sidebar
// =============================================================================

struct SidebarView: View {
    // -------------------------------------------------------------------------
    // @ObservedObject: This view RECEIVES the ViewModel from parent
    // -------------------------------------------------------------------------
    @ObservedObject var viewModel: PlannerViewModel

    var body: some View {
        List(selection: $viewModel.selectedSidebarItem) {
            // -----------------------------------------------------------------
            // Main Navigation Section
            // -----------------------------------------------------------------
            Section("Navigation") {
                // Today
                Label("Today", systemImage: "sun.max.fill")
                    .tag(SidebarItem.today)

                // This Week
                Label("This Week", systemImage: "calendar")
                    .tag(SidebarItem.thisWeek)
            }

            // -----------------------------------------------------------------
            // Subjects Section
            // -----------------------------------------------------------------
            Section("Subjects") {
                // All Subjects link
                Label("All Subjects", systemImage: "books.vertical.fill")
                    .tag(SidebarItem.subjects)

                // Individual subjects
                ForEach(viewModel.subjects) { subject in
                    HStack {
                        // Colour indicator
                        Circle()
                            .fill(Color(hex: subject.colour ?? "#666666"))
                            .frame(width: 12, height: 12)

                        Text(subject.name)
                            .lineLimit(1)
                    }
                    .tag(SidebarItem.subject(subject))
                }
            }
        }
        .navigationTitle("Planner")
        .listStyle(.sidebar)
    }
}

// =============================================================================
// DetailContentView - Content Based on Sidebar Selection
// =============================================================================

struct DetailContentView: View {
    @ObservedObject var viewModel: PlannerViewModel

    var body: some View {
        // Show different content based on what's selected in sidebar
        switch viewModel.selectedSidebarItem {
        case .today:
            TodayView(viewModel: viewModel)

        case .thisWeek:
            WeekView(viewModel: viewModel)

        case .subjects:
            SubjectsListView(viewModel: viewModel)

        case .subject(let subject):
            SubjectDetailView(viewModel: viewModel, subject: subject)

        case nil:
            // Nothing selected - show placeholder
            ContentUnavailableView(
                "Select an Item",
                systemImage: "sidebar.left",
                description: Text("Choose an option from the sidebar")
            )
        }
    }
}

// =============================================================================
// TodayView - Today's Lessons
// =============================================================================

struct TodayView: View {
    @ObservedObject var viewModel: PlannerViewModel
    @State private var selectedLessonForSheet: Lesson?

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            // Lessons list
            if viewModel.getTodayLessons().isEmpty {
                ContentUnavailableView(
                    "No Lessons Today",
                    systemImage: "calendar.badge.checkmark",
                    description: Text("Enjoy your day off!")
                )
            } else {
                List {
                    ForEach(viewModel.getTodayLessons()) { lesson in
                        LessonRowView(
                            lesson: lesson,
                            subject: viewModel.getSubject(id: lesson.subjectId)
                        )
                        .contentShape(Rectangle())
                        .onTapGesture {
                            Task {
                                await viewModel.selectLesson(lesson)
                                selectedLessonForSheet = lesson
                            }
                        }
                    }
                }
                .listStyle(.insetGrouped)
            }
        }
        .navigationTitle("Today")
        .sheet(item: $selectedLessonForSheet) { _ in
            if viewModel.selectedLesson != nil {
                LessonDetailView(viewModel: viewModel)
            }
        }
        .refreshable {
            await viewModel.refreshWeekData()
        }
    }

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(formattedDate)
                    .font(.title2)
                    .fontWeight(.semibold)

                if let weekData = viewModel.weekData,
                   let today = weekData.days.first(where: { $0.date == viewModel.todayDateString }) {
                    Text("\(today.weekLabel) - Day \(today.cycleDay)")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()
        }
        .padding()
        .background(Color(.systemGroupedBackground))
    }

    private var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        guard let date = formatter.date(from: viewModel.todayDateString) else {
            return viewModel.todayDateString
        }
        formatter.dateFormat = "EEEE, MMMM d"
        return formatter.string(from: date)
    }
}

// =============================================================================
// WeekView - This Week's Timetable
// =============================================================================

struct WeekView: View {
    @ObservedObject var viewModel: PlannerViewModel
    @State private var selectedLessonForSheet: Lesson?

    var body: some View {
        VStack(spacing: 0) {
            // Week navigation
            weekNavigationBar

            // Week grid or list
            if let weekData = viewModel.weekData {
                List {
                    ForEach(weekData.days) { day in
                        Section {
                            if day.lessons.isEmpty {
                                Text("No lessons scheduled")
                                    .foregroundStyle(.secondary)
                                    .italic()
                            } else {
                                ForEach(day.lessons.sorted { $0.period < $1.period }) { lesson in
                                    LessonRowView(
                                        lesson: lesson,
                                        subject: viewModel.getSubject(id: lesson.subjectId)
                                    )
                                    .contentShape(Rectangle())
                                    .onTapGesture {
                                        Task {
                                            await viewModel.selectLesson(lesson)
                                            selectedLessonForSheet = lesson
                                        }
                                    }
                                }
                            }
                        } header: {
                            HStack {
                                Text(day.weekdayName)
                                    .fontWeight(.semibold)
                                Spacer()
                                Text("Day \(day.cycleDay)")
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 2)
                                    .background(day.isWeekA ? Color.blue.opacity(0.2) : Color.green.opacity(0.2))
                                    .clipShape(Capsule())
                            }
                        }
                    }
                }
                .listStyle(.insetGrouped)
            } else {
                ProgressView("Loading...")
            }
        }
        .navigationTitle(viewModel.weekData?.primaryWeek ?? "This Week")
        .sheet(item: $selectedLessonForSheet) { _ in
            if viewModel.selectedLesson != nil {
                LessonDetailView(viewModel: viewModel)
            }
        }
        .refreshable {
            await viewModel.refreshWeekData()
        }
    }

    private var weekNavigationBar: some View {
        HStack {
            Button {
                Task { await viewModel.goToPreviousWeek() }
            } label: {
                Image(systemName: "chevron.left")
                Text("Prev")
            }

            Spacer()

            Button("Today") {
                Task { await viewModel.goToCurrentWeek() }
            }
            .buttonStyle(.bordered)

            Spacer()

            Button {
                Task { await viewModel.goToNextWeek() }
            } label: {
                Text("Next")
                Image(systemName: "chevron.right")
            }
        }
        .padding()
        .background(Color(.systemGroupedBackground))
    }
}

// =============================================================================
// LessonRowView - Single Lesson in a List
// =============================================================================

struct LessonRowView: View {
    let lesson: Lesson
    let subject: Subject?

    var body: some View {
        HStack(spacing: 12) {
            // Period number
            Text("P\(lesson.period)")
                .font(.headline)
                .frame(width: 40)
                .foregroundStyle(.secondary)

            // Colour indicator
            RoundedRectangle(cornerRadius: 4)
                .fill(Color(hex: subject?.colour ?? "#666666"))
                .frame(width: 4, height: 40)

            // Subject info
            VStack(alignment: .leading, spacing: 4) {
                Text(subject?.name ?? "Unknown Subject")
                    .font(.headline)

                if let title = lesson.title {
                    Text(title)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            // Indicators
            HStack(spacing: 8) {
                if let notes = lesson.notes, !notes.isEmpty {
                    Label("\(notes.count)", systemImage: "note.text")
                        .font(.caption)
                        .foregroundStyle(.blue)
                }

                if let todos = lesson.todos {
                    let incomplete = todos.filter { !$0.isCompleted }.count
                    if incomplete > 0 {
                        Label("\(incomplete)", systemImage: "checklist")
                            .font(.caption)
                            .foregroundStyle(.orange)
                    }
                }
            }

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .padding(.vertical, 4)
    }
}

// =============================================================================
// SubjectsListView - All Subjects
// =============================================================================

struct SubjectsListView: View {
    @ObservedObject var viewModel: PlannerViewModel

    var body: some View {
        List {
            ForEach(viewModel.subjects) { subject in
                NavigationLink(value: subject) {
                    HStack {
                        Circle()
                            .fill(Color(hex: subject.colour ?? "#666666"))
                            .frame(width: 16, height: 16)

                        VStack(alignment: .leading) {
                            Text(subject.name)
                                .font(.headline)

                            if let code = subject.code {
                                Text(code)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        Spacer()

                        if let room = subject.room {
                            Text(room)
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color(.systemGray5))
                                .clipShape(Capsule())
                        }
                    }
                }
            }
        }
        .navigationTitle("Subjects")
    }
}

// =============================================================================
// SubjectDetailView - Single Subject Detail
// =============================================================================

struct SubjectDetailView: View {
    @ObservedObject var viewModel: PlannerViewModel
    let subject: Subject

    var body: some View {
        List {
            // Subject info section
            Section("Details") {
                if let code = subject.code {
                    LabeledContent("Code", value: code)
                }
                if let yearLevel = subject.yearLevel {
                    LabeledContent("Year Level", value: "Year \(yearLevel)")
                }
                if let room = subject.room {
                    LabeledContent("Room", value: room)
                }
                LabeledContent("Semester", value: "Semester \(subject.semester)")
            }

            // Lessons for this subject
            Section("This Week's Lessons") {
                let lessons = viewModel.getLessonsForSubject(subject)
                if lessons.isEmpty {
                    Text("No lessons this week")
                        .foregroundStyle(.secondary)
                        .italic()
                } else {
                    ForEach(lessons) { lesson in
                        HStack {
                            Text(lesson.date)
                                .font(.subheadline)
                            Text("Period \(lesson.period)")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle(subject.name)
    }
}

// =============================================================================
// Color Extension - Parse Hex Colors
// =============================================================================

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 128, 128, 128)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// =============================================================================
// Preview
// =============================================================================

#Preview {
    ContentView()
}
