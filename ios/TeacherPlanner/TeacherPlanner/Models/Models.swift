// =============================================================================
// Models.swift - Data Models for Teacher Planner
// =============================================================================
// These models mirror the backend's database schema and API responses.
// They conform to Codable for JSON encoding/decoding and Identifiable
// for use in SwiftUI Lists and ForEach.
//
// SWIFT CONCEPTS USED:
// --------------------
// - struct: Value types that are copied when passed around
// - Codable: Protocol for JSON encoding/decoding
// - Identifiable: Protocol requiring an 'id' property for SwiftUI
// - CodingKeys: Enum to map JSON keys to Swift property names
// =============================================================================

import Foundation

// =============================================================================
// MARK: - Settings
// =============================================================================
// Application-wide settings from the backend.

struct Settings: Codable, Identifiable {
    let id: Int
    let periodsPerDay: Int
    let currentYear: Int
    let currentSemester: Int
    let cycleLength: Int
    let cycleStartDate: String?  // ISO date string, e.g., "2025-01-27"

    // -------------------------------------------------------------------------
    // CodingKeys: Map JSON snake_case to Swift camelCase
    // -------------------------------------------------------------------------
    // The backend uses snake_case (periods_per_day), but Swift convention
    // is camelCase (periodsPerDay). CodingKeys handles this mapping.
    // -------------------------------------------------------------------------
    enum CodingKeys: String, CodingKey {
        case id
        case periodsPerDay = "periods_per_day"
        case currentYear = "current_year"
        case currentSemester = "current_semester"
        case cycleLength = "cycle_length"
        case cycleStartDate = "cycle_start_date"
    }
}

// =============================================================================
// MARK: - Subject
// =============================================================================
// A subject/class being taught, e.g., "Year 11 Modern History"

struct Subject: Codable, Identifiable {
    let id: Int
    let name: String
    let code: String?
    let yearLevel: Int?
    let academicYear: Int
    let semester: Int
    let room: String?
    let colour: String?
    let notes: String?
    let isActive: Bool
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, name, code, room, colour, notes, semester
        case yearLevel = "year_level"
        case academicYear = "academic_year"
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// =============================================================================
// MARK: - Note
// =============================================================================
// A note attached to a lesson.

struct Note: Codable, Identifiable {
    let id: Int
    let lessonId: Int
    let title: String?
    let content: String
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, title, content
        case lessonId = "lesson_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// =============================================================================
// MARK: - Resource
// =============================================================================
// A resource (link, file reference) attached to a lesson.

struct Resource: Codable, Identifiable {
    let id: Int
    let lessonId: Int
    let title: String
    let url: String?
    let filePath: String?
    let resourceType: String?
    let description: String?
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, title, url, description
        case lessonId = "lesson_id"
        case filePath = "file_path"
        case resourceType = "resource_type"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// =============================================================================
// MARK: - Todo
// =============================================================================
// A to-do item attached to a lesson.

struct Todo: Codable, Identifiable {
    let id: Int
    let lessonId: Int
    let content: String
    var isCompleted: Bool  // 'var' because we modify this locally
    let completedAt: String?
    let priority: Int?
    let dueDate: String?
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, content, priority
        case lessonId = "lesson_id"
        case isCompleted = "is_completed"
        case completedAt = "completed_at"
        case dueDate = "due_date"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// =============================================================================
// MARK: - Lesson
// =============================================================================
// The core entity - a specific lesson instance on a date/period.

struct Lesson: Codable, Identifiable {
    let id: Int
    let date: String
    let period: Int
    let subjectId: Int
    let cycleDay: Int?
    let title: String?
    let createdAt: String
    let updatedAt: String

    // Nested items (included in detail responses)
    var notes: [Note]?
    var resources: [Resource]?
    var todos: [Todo]?
    var subject: Subject?

    enum CodingKeys: String, CodingKey {
        case id, date, period, title, notes, resources, todos, subject
        case subjectId = "subject_id"
        case cycleDay = "cycle_day"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

// =============================================================================
// MARK: - Day Info (for week timetable)
// =============================================================================
// Information about a single day in the timetable.

struct DayInfo: Codable, Identifiable {
    // Use date as the ID since it's unique within a week
    var id: String { date }

    let date: String
    let weekday: Int
    let weekdayName: String
    let cycleDay: Int
    let isWeekA: Bool
    let weekLabel: String
    let lessons: [Lesson]

    enum CodingKeys: String, CodingKey {
        case date, weekday, lessons
        case weekdayName = "weekday_name"
        case cycleDay = "cycle_day"
        case isWeekA = "is_week_a"
        case weekLabel = "week_label"
    }
}

// =============================================================================
// MARK: - Week Timetable
// =============================================================================
// Full week's timetable data from the API.

struct WeekTimetable: Codable {
    let weekStart: String
    let weekEnd: String
    let primaryWeek: String
    let periodsPerDay: Int
    let days: [DayInfo]

    enum CodingKeys: String, CodingKey {
        case days
        case weekStart = "week_start"
        case weekEnd = "week_end"
        case primaryWeek = "primary_week"
        case periodsPerDay = "periods_per_day"
    }
}

// =============================================================================
// MARK: - Request Models (for creating/updating)
// =============================================================================
// These models are used when sending data TO the API.

struct CreateNoteRequest: Codable {
    let title: String?
    let content: String
}

struct CreateTodoRequest: Codable {
    let content: String
    let priority: Int?
    let dueDate: String?

    enum CodingKeys: String, CodingKey {
        case content, priority
        case dueDate = "due_date"
    }
}

struct CreateResourceRequest: Codable {
    let title: String
    let url: String?
    let resourceType: String?

    enum CodingKeys: String, CodingKey {
        case title, url
        case resourceType = "resource_type"
    }
}

struct CreateLessonRequest: Codable {
    let date: String
    let period: Int
    let subjectId: Int
    let title: String?

    enum CodingKeys: String, CodingKey {
        case date, period, title
        case subjectId = "subject_id"
    }
}
