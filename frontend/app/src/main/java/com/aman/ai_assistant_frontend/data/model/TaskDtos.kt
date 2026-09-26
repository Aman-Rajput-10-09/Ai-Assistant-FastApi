package com.aman.ai_assistant_frontend.data.model

import com.google.gson.annotations.SerializedName

data class TaskDto(
    @SerializedName("id") val id: Int,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String?,
    @SerializedName("due_date") val dueDate: String?,
    @SerializedName("priority") val priority: String,
    @SerializedName("status") val status: String,
    @SerializedName("is_recurring") val isRecurring: Boolean?,
    @SerializedName("user_id") val userId: Int?,
    @SerializedName("category_id") val categoryId: Int?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("updated_at") val updatedAt: String?
)

data class TaskCreateDto(
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String? = null,
    @SerializedName("due_date") val dueDate: String? = null,
    @SerializedName("priority") val priority: String = "normal",
    @SerializedName("category_id") val categoryId: Int? = null
)

data class TaskUpdateDto(
    @SerializedName("title") val title: String? = null,
    @SerializedName("description") val description: String? = null,
    @SerializedName("due_date") val dueDate: String? = null,
    @SerializedName("priority") val priority: String? = null,
    @SerializedName("status") val status: String? = null,
    @SerializedName("category_id") val categoryId: Int? = null
)
