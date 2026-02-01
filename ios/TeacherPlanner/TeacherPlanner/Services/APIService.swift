// =============================================================================
// APIService.swift - Network Communication with Backend
// =============================================================================
// This service handles all HTTP requests to the Teacher Planner backend API.
//
// SWIFT CONCEPTS USED:
// --------------------
// - async/await: Modern Swift concurrency for asynchronous operations
// - Generics: The request<T> function works with any Codable type
// - Result type: Could be used for explicit error handling (we use throws)
// - URLSession: Apple's networking API
//
// USAGE:
// ------
// let service = APIService.shared  // Singleton instance
// let settings = try await service.getSettings()
// =============================================================================

import Foundation

// =============================================================================
// APIError - Custom Error Types
// =============================================================================
// Define specific errors that can occur during API calls.

enum APIError: LocalizedError {
    case invalidURL
    case networkError(Error)
    case invalidResponse
    case httpError(statusCode: Int, message: String?)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let statusCode, let message):
            return "HTTP \(statusCode): \(message ?? "Unknown error")"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        }
    }
}

// =============================================================================
// APIService - Main Service Class
// =============================================================================

class APIService {
    // -------------------------------------------------------------------------
    // Singleton Pattern
    // -------------------------------------------------------------------------
    // A singleton ensures only one instance exists throughout the app.
    // Access it via APIService.shared from anywhere.
    // -------------------------------------------------------------------------
    static let shared = APIService()

    // -------------------------------------------------------------------------
    // Configuration
    // -------------------------------------------------------------------------
    // The base URL of your backend server.
    // For local development, this would be your Mac's IP address.
    // For production, this would be your Unraid server's address.
    // -------------------------------------------------------------------------
    private let baseURL: String

    // JSON decoder configured for our date format
    private let decoder: JSONDecoder

    // JSON encoder for sending data
    private let encoder: JSONEncoder

    // -------------------------------------------------------------------------
    // Initializer
    // -------------------------------------------------------------------------
    private init() {
        // TODO: Make this configurable via Settings app or config file
        // For now, use localhost (works in simulator) or your server IP
        self.baseURL = "http://localhost:8000"

        // Configure JSON decoder
        self.decoder = JSONDecoder()

        // Configure JSON encoder
        self.encoder = JSONEncoder()
    }

    // -------------------------------------------------------------------------
    // Configure Base URL
    // -------------------------------------------------------------------------
    // Call this to change the server URL (e.g., from a settings screen)
    func configure(baseURL: String) -> APIService {
        // Note: In a real app, you'd want to persist this
        // For now, we return a new instance (or modify shared)
        return self
    }

    // =========================================================================
    // MARK: - Generic Request Methods
    // =========================================================================
    // These are the core methods that all API calls use.
    // They're generic over T: Decodable (response) and B: Encodable (request body).
    //
    // WHY TWO METHODS?
    // ----------------
    // Swift cannot encode "existential types" (like `Codable?` or `any Codable`).
    // If we wrote `body: Codable?`, the compiler would fail at encoder.encode(body)
    // because it doesn't know the concrete type at compile time.
    //
    // Solution: Use generics! We have:
    // 1. request<T>(endpoint:method:) - For requests WITHOUT a body (GET, DELETE)
    // 2. request<T, B>(endpoint:method:body:) - For requests WITH a body (POST, PUT)
    //
    // With generics, Swift knows the exact type at compile time and can encode it.
    //
    // ASYNC/AWAIT EXPLANATION:
    // ------------------------
    // - 'async' means this function performs asynchronous work
    // - 'throws' means it can throw errors
    // - Callers must use 'try await' to call this function
    // - The function suspends at 'await' points without blocking the thread
    // =========================================================================

    /// Request WITHOUT a body (for GET requests)
    private func request<T: Decodable>(
        endpoint: String,
        method: String = "GET"
    ) async throws -> T {
        // Build the URL
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        // Create the request
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Make the network call
        // 'await' suspends here until the network call completes
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        // Check HTTP status code
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // Handle error status codes
        if httpResponse.statusCode < 200 || httpResponse.statusCode >= 300 {
            // Try to decode error message from response
            let errorMessage = try? decoder.decode([String: String].self, from: data)["detail"]
            throw APIError.httpError(
                statusCode: httpResponse.statusCode,
                message: errorMessage
            )
        }

        // Handle 204 No Content (for DELETE requests)
        if httpResponse.statusCode == 204 {
            // Return an empty instance if possible, or throw if T doesn't support it
            // For most cases, we won't call this with an expected return type for DELETE
            if let emptyResult = Optional<T>.none as? T {
                return emptyResult
            }
        }

        // Decode the response
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    /// Request WITH a body (for POST, PUT, PATCH requests)
    /// B: Encodable is a generic type parameter - the compiler knows the exact type
    /// at compile time, allowing proper encoding.
    private func request<T: Decodable, B: Encodable>(
        endpoint: String,
        method: String,
        body: B
    ) async throws -> T {
        // Build the URL
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        // Create the request
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Encode the body - this works because B is a concrete generic type!
        request.httpBody = try encoder.encode(body)

        // Make the network call
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        // Check HTTP status code
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // Handle error status codes
        if httpResponse.statusCode < 200 || httpResponse.statusCode >= 300 {
            let errorMessage = try? decoder.decode([String: String].self, from: data)["detail"]
            throw APIError.httpError(
                statusCode: httpResponse.statusCode,
                message: errorMessage
            )
        }

        // Decode the response
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    // Special version for requests that don't return data (DELETE)
    private func requestNoContent(
        endpoint: String,
        method: String = "DELETE"
    ) async throws {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (_, response): (Data, URLResponse)
        do {
            (_, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if httpResponse.statusCode < 200 || httpResponse.statusCode >= 300 {
            throw APIError.httpError(statusCode: httpResponse.statusCode, message: nil)
        }
    }

    // =========================================================================
    // MARK: - Settings Endpoints
    // =========================================================================

    func getSettings() async throws -> Settings {
        return try await request(endpoint: "/settings")
    }

    func updateSettings(_ settings: [String: Any]) async throws -> Settings {
        // For partial updates, we need a flexible approach
        // This is a simplified version
        let jsonData = try JSONSerialization.data(withJSONObject: settings)
        guard let url = URL(string: "\(baseURL)/settings") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = jsonData

        let (data, _) = try await URLSession.shared.data(for: request)
        return try decoder.decode(Settings.self, from: data)
    }

    // =========================================================================
    // MARK: - Subjects Endpoints
    // =========================================================================

    func getSubjects(isActive: Bool? = nil) async throws -> [Subject] {
        var endpoint = "/subjects"
        if let isActive = isActive {
            endpoint += "?is_active=\(isActive)"
        }
        return try await request(endpoint: endpoint)
    }

    func getSubject(id: Int) async throws -> Subject {
        return try await request(endpoint: "/subjects/\(id)")
    }

    // =========================================================================
    // MARK: - Lessons Endpoints
    // =========================================================================

    /// Get the timetable for a specific week
    /// - Parameter startDate: The Monday of the week (YYYY-MM-DD format)
    func getWeekTimetable(startDate: String) async throws -> WeekTimetable {
        return try await request(endpoint: "/lessons/week?start_date=\(startDate)")
    }

    /// Get a specific lesson with all its details
    func getLesson(id: Int) async throws -> Lesson {
        return try await request(endpoint: "/lessons/\(id)")
    }

    /// Create a new lesson
    func createLesson(_ lesson: CreateLessonRequest) async throws -> Lesson {
        return try await request(
            endpoint: "/lessons",
            method: "POST",
            body: lesson
        )
    }

    /// Update a lesson's subject assignment
    /// Note: We use UpdateLessonRequest struct instead of a dictionary because
    /// Swift's generic system needs concrete types for encoding - dictionaries
    /// don't satisfy the Encodable constraint properly in generic contexts.
    func updateLesson(id: Int, subjectId: Int) async throws -> Lesson {
        return try await request(
            endpoint: "/lessons/\(id)",
            method: "PUT",
            body: UpdateLessonRequest(subjectId: subjectId)
        )
    }

    // =========================================================================
    // MARK: - Notes Endpoints
    // =========================================================================

    func createNote(lessonId: Int, note: CreateNoteRequest) async throws -> Note {
        return try await request(
            endpoint: "/lessons/\(lessonId)/notes",
            method: "POST",
            body: note
        )
    }

    func deleteNote(lessonId: Int, noteId: Int) async throws {
        try await requestNoContent(
            endpoint: "/lessons/\(lessonId)/notes/\(noteId)"
        )
    }

    // =========================================================================
    // MARK: - Resources Endpoints
    // =========================================================================

    func createResource(lessonId: Int, resource: CreateResourceRequest) async throws -> Resource {
        return try await request(
            endpoint: "/lessons/\(lessonId)/resources",
            method: "POST",
            body: resource
        )
    }

    func deleteResource(lessonId: Int, resourceId: Int) async throws {
        try await requestNoContent(
            endpoint: "/lessons/\(lessonId)/resources/\(resourceId)"
        )
    }

    // =========================================================================
    // MARK: - Todos Endpoints
    // =========================================================================

    func createTodo(lessonId: Int, todo: CreateTodoRequest) async throws -> Todo {
        return try await request(
            endpoint: "/lessons/\(lessonId)/todos",
            method: "POST",
            body: todo
        )
    }

    /// Toggle a todo's completion status
    /// This is the key endpoint for checking off items!
    func toggleTodo(lessonId: Int, todoId: Int) async throws -> Todo {
        return try await request(
            endpoint: "/lessons/\(lessonId)/todos/\(todoId)/toggle",
            method: "PATCH"
        )
    }

    func deleteTodo(lessonId: Int, todoId: Int) async throws {
        try await requestNoContent(
            endpoint: "/lessons/\(lessonId)/todos/\(todoId)"
        )
    }
}

// =============================================================================
// NOTE: Dictionary Encodable Extension Removed
// =============================================================================
// We previously had an extension to make [String: Any] Encodable, but this
// approach has problems:
//
// 1. TYPE MISMATCH: Dictionary literals like ["key": 1] create [String: Int],
//    not [String: Any], so the extension wouldn't apply.
//
// 2. GENERIC CONSTRAINTS: Even with the extension, passing dictionaries to
//    generic functions with Encodable constraints doesn't work well because
//    Swift can't prove at compile time that the extension applies.
//
// 3. BEST PRACTICE: Using dedicated Codable structs (like UpdateLessonRequest)
//    is cleaner, type-safe, and provides better documentation of the API.
//
// All request bodies now use proper Codable structs defined in Models.swift.
// =============================================================================
