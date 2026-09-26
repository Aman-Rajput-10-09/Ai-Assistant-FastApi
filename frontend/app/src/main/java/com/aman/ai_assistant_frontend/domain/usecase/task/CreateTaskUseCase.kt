package com.aman.ai_assistant_frontend.domain.usecase.task

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.Task
import com.aman.ai_assistant_frontend.domain.model.TaskPriority
import com.aman.ai_assistant_frontend.domain.repository.TaskRepository
import javax.inject.Inject

class CreateTaskUseCase @Inject constructor(
    private val taskRepository: TaskRepository
) {
    suspend operator fun invoke(
        title: String,
        description: String? = null,
        dueDate: String? = null,
        priority: TaskPriority = TaskPriority.NORMAL
    ): NetworkResult<Task> {
        if (title.isBlank()) return NetworkResult.Error("Task title cannot be empty")
        return taskRepository.createTask(title, description, dueDate, priority)
    }
}
