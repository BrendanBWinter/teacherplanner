// =============================================================================
// LessonDetailView.swift - Detailed View of a Lesson
// =============================================================================
// This view shows all details for a selected lesson:
// - Subject information
// - List of Notes
// - List of Resources
// - Checklist of To-Dos
//
// OBSERVABLEOBJECT IN ACTION - TODO TOGGLE EXAMPLE:
// =================================================
//
// When you tap a checkbox to mark a To-Do as complete, here's what happens:
//
// 1. USER TAPS CHECKBOX
//    └─> The Toggle onChange handler fires
//
// 2. CALL VIEWMODEL METHOD
//    └─> Task { await viewModel.toggleTodo(todo) }
//
// 3. VIEWMODEL UPDATES
//    └─> toggleTodo() calls APIService.toggleTodo()
//    └─> API updates the backend database
//    └─> toggleTodo() calls refreshSelectedLesson()
//    └─> refreshSelectedLesson() fetches fresh data
//    └─> self.selectedLesson = freshLesson  <-- @Published triggers!
//
// 4. SWIFTUI DETECTS CHANGE
//    └─> The @Published property changed
//    └─> SwiftUI schedules a re-render
//
// 5. VIEW RE-RENDERS
//    └─> LessonDetailView body is called again
//    └─> ForEach over viewModel.selectedLesson?.todos
//    └─> The checkbox now shows the updated isCompleted state!
//
// This entire flow happens automatically because:
// - PlannerViewModel conforms to ObservableObject
// - selectedLesson is marked @Published
// - LessonDetailView observes the ViewModel via @ObservedObject
// =============================================================================

import SwiftUI

struct LessonDetailView: View {
    // -------------------------------------------------------------------------
    // @ObservedObject: We observe the ViewModel for changes
    // -------------------------------------------------------------------------
    // When viewModel.selectedLesson changes (because @Published triggers),
    // this view automatically re-renders to show the new data.
    // -------------------------------------------------------------------------
    @ObservedObject var viewModel: PlannerViewModel

    // For dismissing the sheet
    @Environment(\.dismiss) private var dismiss

    // State for add forms
    @State private var showingAddNote = false
    @State private var showingAddTodo = false
    @State private var showingAddResource = false

    // Form input state
    @State private var newNoteTitle = ""
    @State private var newNoteContent = ""
    @State private var newTodoContent = ""
    @State private var newResourceTitle = ""
    @State private var newResourceURL = ""

    var body: some View {
        NavigationStack {
            if let lesson = viewModel.selectedLesson {
                List {
                    // ---------------------------------------------------------
                    // Subject Section
                    // ---------------------------------------------------------
                    subjectSection(lesson: lesson)

                    // ---------------------------------------------------------
                    // Notes Section
                    // ---------------------------------------------------------
                    notesSection(lesson: lesson)

                    // ---------------------------------------------------------
                    // Resources Section
                    // ---------------------------------------------------------
                    resourcesSection(lesson: lesson)

                    // ---------------------------------------------------------
                    // To-Dos Section - THE KEY EXAMPLE
                    // ---------------------------------------------------------
                    todosSection(lesson: lesson)
                }
                .listStyle(.insetGrouped)
                .navigationTitle("Lesson Details")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Done") {
                            viewModel.clearSelectedLesson()
                            dismiss()
                        }
                    }
                }
            } else {
                ProgressView("Loading...")
            }
        }
        // Add Note Sheet
        .sheet(isPresented: $showingAddNote) {
            addNoteSheet
        }
        // Add Todo Sheet
        .sheet(isPresented: $showingAddTodo) {
            addTodoSheet
        }
        // Add Resource Sheet
        .sheet(isPresented: $showingAddResource) {
            addResourceSheet
        }
    }

    // =========================================================================
    // MARK: - Subject Section
    // =========================================================================

    @ViewBuilder
    private func subjectSection(lesson: Lesson) -> some View {
        Section {
            if let subject = viewModel.getSubject(id: lesson.subjectId) {
                HStack {
                    Circle()
                        .fill(Color(hex: subject.colour ?? "#666666"))
                        .frame(width: 20, height: 20)

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

            // Lesson info
            LabeledContent("Date", value: lesson.date)
            LabeledContent("Period", value: "Period \(lesson.period)")

            if let cycleDay = lesson.cycleDay {
                LabeledContent("Cycle Day", value: "Day \(cycleDay)")
            }

            if let title = lesson.title {
                LabeledContent("Topic", value: title)
            }
        } header: {
            Text("Subject")
        }
    }

    // =========================================================================
    // MARK: - Notes Section
    // =========================================================================

    @ViewBuilder
    private func notesSection(lesson: Lesson) -> some View {
        Section {
            if let notes = lesson.notes, !notes.isEmpty {
                ForEach(notes) { note in
                    VStack(alignment: .leading, spacing: 4) {
                        if let title = note.title {
                            Text(title)
                                .font(.headline)
                        }
                        Text(note.content)
                            .font(.body)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 4)
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        Button(role: .destructive) {
                            Task { await viewModel.deleteNote(note) }
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    }
                }
            } else {
                Text("No notes yet")
                    .foregroundStyle(.secondary)
                    .italic()
            }

            // Add Note button
            Button {
                showingAddNote = true
            } label: {
                Label("Add Note", systemImage: "plus.circle.fill")
            }
        } header: {
            HStack {
                Text("Notes")
                Spacer()
                Text("\(lesson.notes?.count ?? 0)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    // =========================================================================
    // MARK: - Resources Section
    // =========================================================================

    @ViewBuilder
    private func resourcesSection(lesson: Lesson) -> some View {
        Section {
            if let resources = lesson.resources, !resources.isEmpty {
                ForEach(resources) { resource in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(resource.title)
                            .font(.headline)

                        if let url = resource.url {
                            Link(destination: URL(string: url) ?? URL(string: "about:blank")!) {
                                Text(url)
                                    .font(.caption)
                                    .lineLimit(1)
                            }
                        }

                        if let description = resource.description {
                            Text(description)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        Button(role: .destructive) {
                            Task { await viewModel.deleteResource(resource) }
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    }
                }
            } else {
                Text("No resources yet")
                    .foregroundStyle(.secondary)
                    .italic()
            }

            // Add Resource button
            Button {
                showingAddResource = true
            } label: {
                Label("Add Resource", systemImage: "plus.circle.fill")
            }
        } header: {
            HStack {
                Text("Resources")
                Spacer()
                Text("\(lesson.resources?.count ?? 0)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    // =========================================================================
    // MARK: - To-Dos Section
    // =========================================================================
    // This section demonstrates ObservableObject in action!
    //
    // Each todo has a Toggle (checkbox). When tapped:
    // 1. The onChange handler calls viewModel.toggleTodo()
    // 2. The ViewModel updates the backend and refreshes data
    // 3. @Published selectedLesson changes
    // 4. SwiftUI re-renders this section with updated checkbox state
    // =========================================================================

    @ViewBuilder
    private func todosSection(lesson: Lesson) -> some View {
        Section {
            if let todos = lesson.todos, !todos.isEmpty {
                ForEach(todos) { todo in
                    // ---------------------------------------------------------
                    // Todo Row with Checkbox
                    // ---------------------------------------------------------
                    HStack {
                        // -------------------------------------------------
                        // THE CHECKBOX (Toggle)
                        // -------------------------------------------------
                        // When this is tapped, SwiftUI calls onChange.
                        // We then call viewModel.toggleTodo() which:
                        // 1. Calls the API
                        // 2. Updates @Published selectedLesson
                        // 3. Triggers re-render
                        // 4. This Toggle now shows new state!
                        // -------------------------------------------------
                        Button {
                            // Use Task to call async method from sync context
                            Task {
                                await viewModel.toggleTodo(todo)
                            }
                        } label: {
                            Image(systemName: todo.isCompleted ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(todo.isCompleted ? .green : .secondary)
                                .font(.title2)
                        }
                        .buttonStyle(.plain)

                        // Todo content
                        VStack(alignment: .leading) {
                            Text(todo.content)
                                .strikethrough(todo.isCompleted)
                                .foregroundStyle(todo.isCompleted ? .secondary : .primary)

                            if let dueDate = todo.dueDate {
                                Text("Due: \(dueDate)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        Spacer()

                        // Priority indicator
                        if let priority = todo.priority {
                            priorityBadge(priority: priority)
                        }
                    }
                    .padding(.vertical, 4)
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        Button(role: .destructive) {
                            Task { await viewModel.deleteTodo(todo) }
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    }
                }
            } else {
                Text("No to-dos yet")
                    .foregroundStyle(.secondary)
                    .italic()
            }

            // Add Todo button
            Button {
                showingAddTodo = true
            } label: {
                Label("Add To-Do", systemImage: "plus.circle.fill")
            }
        } header: {
            HStack {
                Text("To-Dos")
                Spacer()
                if let todos = lesson.todos {
                    let incomplete = todos.filter { !$0.isCompleted }.count
                    Text("\(incomplete) remaining")
                        .font(.caption)
                        .foregroundStyle(incomplete > 0 ? .orange : .green)
                }
            }
        }
    }

    // Priority badge helper
    @ViewBuilder
    private func priorityBadge(priority: Int) -> some View {
        let (text, color): (String, Color) = {
            switch priority {
            case 1: return ("High", .red)
            case 2: return ("Med", .orange)
            case 3: return ("Low", .blue)
            default: return ("", .clear)
            }
        }()

        if !text.isEmpty {
            Text(text)
                .font(.caption2)
                .fontWeight(.semibold)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(color.opacity(0.2))
                .foregroundStyle(color)
                .clipShape(Capsule())
        }
    }

    // =========================================================================
    // MARK: - Add Sheets
    // =========================================================================

    private var addNoteSheet: some View {
        NavigationStack {
            Form {
                TextField("Title (optional)", text: $newNoteTitle)
                TextEditor(text: $newNoteContent)
                    .frame(minHeight: 150)
            }
            .navigationTitle("Add Note")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") {
                        resetNoteForm()
                        showingAddNote = false
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Save") {
                        Task {
                            await viewModel.addNote(
                                title: newNoteTitle.isEmpty ? nil : newNoteTitle,
                                content: newNoteContent
                            )
                            resetNoteForm()
                            showingAddNote = false
                        }
                    }
                    .disabled(newNoteContent.isEmpty)
                }
            }
        }
    }

    private var addTodoSheet: some View {
        NavigationStack {
            Form {
                TextField("What needs to be done?", text: $newTodoContent)
            }
            .navigationTitle("Add To-Do")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") {
                        newTodoContent = ""
                        showingAddTodo = false
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Save") {
                        Task {
                            await viewModel.addTodo(content: newTodoContent)
                            newTodoContent = ""
                            showingAddTodo = false
                        }
                    }
                    .disabled(newTodoContent.isEmpty)
                }
            }
        }
    }

    private var addResourceSheet: some View {
        NavigationStack {
            Form {
                TextField("Title", text: $newResourceTitle)
                TextField("URL (optional)", text: $newResourceURL)
                    .keyboardType(.URL)
                    .autocapitalization(.none)
            }
            .navigationTitle("Add Resource")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") {
                        resetResourceForm()
                        showingAddResource = false
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Save") {
                        Task {
                            await viewModel.addResource(
                                title: newResourceTitle,
                                url: newResourceURL.isEmpty ? nil : newResourceURL
                            )
                            resetResourceForm()
                            showingAddResource = false
                        }
                    }
                    .disabled(newResourceTitle.isEmpty)
                }
            }
        }
    }

    // =========================================================================
    // MARK: - Helpers
    // =========================================================================

    private func resetNoteForm() {
        newNoteTitle = ""
        newNoteContent = ""
    }

    private func resetResourceForm() {
        newResourceTitle = ""
        newResourceURL = ""
    }
}

// =============================================================================
// Preview
// =============================================================================

#Preview {
    LessonDetailView(viewModel: PlannerViewModel())
}
