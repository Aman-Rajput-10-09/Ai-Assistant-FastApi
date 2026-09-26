package com.aman.ai_assistant_frontend.domain.usecase.task

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.repository.TaskRepository
import javax.inject.Inject

class DeleteTaskUseCase @Inject constructor(
    private val taskRepository: TaskRepository
) {
    suspend operator fun invoke(taskId: Int): NetworkResult<Unit> {
        return taskRepository.deleteTask(taskId)
    }
}
