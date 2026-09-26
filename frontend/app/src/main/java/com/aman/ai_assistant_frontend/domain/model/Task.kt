package com.aman.ai_assistant_frontend.domain.model

data class Task(
    val id: Int,
    val title: String,
    val description: String = "",
    val dueDate: String? = null,
    val priority: TaskPriority = TaskPriority.NORMAL,
    val isCompleted: Boolean = false
)

enum class TaskPriority {
    LOW,
    NORMAL,
    HIGH;

    companion object {
        fun fromString(value: String): TaskPriority {
            return when (value.lowercase()) {
                "high" -> HIGH
                "low" -> LOW
                else -> NORMAL
            }
        }
    }
}
