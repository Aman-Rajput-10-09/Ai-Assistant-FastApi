package com.aman.ai_assistant_frontend.domain.usecase.task

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.Task
import com.aman.ai_assistant_frontend.domain.repository.TaskRepository
import javax.inject.Inject

class GetTasksUseCase @Inject constructor(
    private val taskRepository: TaskRepository
) {
    suspend operator fun invoke(status: String? = null): NetworkResult<List<Task>> {
        return taskRepository.getTasks(status)
    }
}
