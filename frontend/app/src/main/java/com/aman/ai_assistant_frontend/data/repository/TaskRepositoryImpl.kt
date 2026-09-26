package com.aman.ai_assistant_frontend.data.repository

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.data.model.TaskCreateDto
import com.aman.ai_assistant_frontend.data.model.TaskDto
import com.aman.ai_assistant_frontend.data.model.TaskUpdateDto
import com.aman.ai_assistant_frontend.data.remote.TaskApiService
import com.aman.ai_assistant_frontend.domain.model.Task
import com.aman.ai_assistant_frontend.domain.model.TaskPriority
import com.aman.ai_assistant_frontend.domain.repository.TaskRepository
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TaskRepositoryImpl @Inject constructor(
    private val taskApiService: TaskApiService
) : TaskRepository {

    override suspend fun getTasks(status: String?): NetworkResult<List<Task>> {
        return try {
            val response = taskApiService.getTasks(status)
            if (response.isSuccessful && response.body() != null) {
                val tasks = response.body()!!.map { it.toDomain() }
                NetworkResult.Success(tasks)
            } else {
                NetworkResult.Error(response.errorBody()?.string() ?: "Failed to fetch tasks", response.code())
            }
        } catch (e: Exception) {
            NetworkResult.Error(e.localizedMessage ?: "Failed to connect to backend")
        }
    }

    override suspend fun createTask(
        title: String,
        description: String?,
        dueDate: String?,
        priority: TaskPriority
    ): NetworkResult<Task> {
        return try {
            val response = taskApiService.createTask(
                TaskCreateDto(
                    title = title.trim(),
                    description = description?.trim(),
                    dueDate = dueDate,
                    priority = priority.name.lowercase()
                )
            )
            if (response.isSuccessful && response.body() != null) {
                NetworkResult.Success(response.body()!!.toDomain())
            } else {
                NetworkResult.Error(response.errorBody()?.string() ?: "Failed to create task", response.code())
            }
        } catch (e: Exception) {
            NetworkResult.Error(e.localizedMessage ?: "Failed to connect to backend")
        }
    }

    override suspend fun updateTaskStatus(taskId: Int, isCompleted: Boolean): NetworkResult<Task> {
        return try {
            val statusString = if (isCompleted) "completed" else "pending"
            val response = taskApiService.updateTask(
                id = taskId,
                task = TaskUpdateDto(status = statusString)
            )
            if (response.isSuccessful && response.body() != null) {
                NetworkResult.Success(response.body()!!.toDomain())
            } else {
                NetworkResult.Error(response.errorBody()?.string() ?: "Failed to update task", response.code())
            }
        } catch (e: Exception) {
            NetworkResult.Error(e.localizedMessage ?: "Failed to connect to backend")
        }
    }

    override suspend fun deleteTask(taskId: Int): NetworkResult<Unit> {
        return try {
            val response = taskApiService.deleteTask(taskId)
            if (response.isSuccessful) {
                NetworkResult.Success(Unit)
            } else {
                NetworkResult.Error(response.errorBody()?.string() ?: "Failed to delete task", response.code())
            }
        } catch (e: Exception) {
            NetworkResult.Error(e.localizedMessage ?: "Failed to connect to backend")
        }
    }

    private fun TaskDto.toDomain(): Task {
        return Task(
            id = id,
            title = title,
            description = description ?: "",
            dueDate = dueDate,
            priority = TaskPriority.fromString(priority),
            isCompleted = status.equals("completed", ignoreCase = true)
        )
    }
}
