package com.aman.ai_assistant_frontend.data.remote

import com.aman.ai_assistant_frontend.core.network.ApiEndpoints
import com.aman.ai_assistant_frontend.data.model.TaskCreateDto
import com.aman.ai_assistant_frontend.data.model.TaskDto
import com.aman.ai_assistant_frontend.data.model.TaskUpdateDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface TaskApiService {

    @GET(ApiEndpoints.TASKS)
    suspend fun getTasks(
        @Query("task_status") status: String? = null
    ): Response<List<TaskDto>>

    @POST(ApiEndpoints.TASKS)
    suspend fun createTask(
        @Body task: TaskCreateDto
    ): Response<TaskDto>

    @PATCH("${ApiEndpoints.TASKS}/{id}")
    suspend fun updateTask(
        @Path("id") id: Int,
        @Body task: TaskUpdateDto
    ): Response<TaskDto>

    @DELETE("${ApiEndpoints.TASKS}/{id}")
    suspend fun deleteTask(
        @Path("id") id: Int
    ): Response<Map<String, String>>
}
