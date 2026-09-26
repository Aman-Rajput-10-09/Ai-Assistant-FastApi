package com.aman.ai_assistant_frontend.domain.repository

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.Task
import com.aman.ai_assistant_frontend.domain.model.TaskPriority

interface TaskRepository {
    suspend fun getTasks(status: String? = null): NetworkResult<List<Task>>
    suspend fun createTask(title: String, description: String?, dueDate: String?, priority: TaskPriority): NetworkResult<Task>
    suspend fun updateTaskStatus(taskId: Int, isCompleted: Boolean): NetworkResult<Task>
    suspend fun deleteTask(taskId: Int): NetworkResult<Unit>
}
