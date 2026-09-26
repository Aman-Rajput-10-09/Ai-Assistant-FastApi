package com.aman.ai_assistant_frontend.presentation.tasks

import com.aman.ai_assistant_frontend.domain.model.Task

data class TasksState(
    val isLoading: Boolean = false,
    val tasks: List<Task> = emptyList(),
    val selectedTab: TaskTab = TaskTab.PENDING,
    val isCreateDialogOpen: Boolean = false,
    val errorMessage: String? = null
)

enum class TaskTab {
    PENDING,
    COMPLETED
}
