package com.aman.ai_assistant_frontend.presentation.tasks

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.Task
import com.aman.ai_assistant_frontend.domain.model.TaskPriority
import com.aman.ai_assistant_frontend.domain.usecase.task.CreateTaskUseCase
import com.aman.ai_assistant_frontend.domain.usecase.task.DeleteTaskUseCase
import com.aman.ai_assistant_frontend.domain.usecase.task.GetTasksUseCase
import com.aman.ai_assistant_frontend.domain.usecase.task.ToggleTaskCompletionUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TasksViewModel @Inject constructor(
    private val getTasksUseCase: GetTasksUseCase,
    private val createTaskUseCase: CreateTaskUseCase,
    private val toggleTaskCompletionUseCase: ToggleTaskCompletionUseCase,
    private val deleteTaskUseCase: DeleteTaskUseCase
) : ViewModel() {

    private val _state = MutableStateFlow(TasksState())
    val state: StateFlow<TasksState> = _state.asStateFlow()

    init {
        loadTasks()
    }

    fun loadTasks() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null) }
            val statusParam = when (_state.value.selectedTab) {
                TaskTab.PENDING -> "pending"
                TaskTab.COMPLETED -> "completed"
            }
            when (val result = getTasksUseCase(statusParam)) {
                is NetworkResult.Success -> {
                    _state.update { it.copy(isLoading = false, tasks = result.data) }
                }
                is NetworkResult.Error -> {
                    _state.update { it.copy(isLoading = false, errorMessage = result.message) }
                }
                is NetworkResult.Loading -> {
                    _state.update { it.copy(isLoading = true) }
                }
            }
        }
    }

    fun selectTab(tab: TaskTab) {
        if (_state.value.selectedTab != tab) {
            _state.update { it.copy(selectedTab = tab) }
            loadTasks()
        }
    }

    fun toggleTask(task: Task) {
        viewModelScope.launch {
            when (val result = toggleTaskCompletionUseCase(task)) {
                is NetworkResult.Success -> {
                    // Refresh task list
                    loadTasks()
                }
                is NetworkResult.Error -> {
                    _state.update { it.copy(errorMessage = result.message) }
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun deleteTask(taskId: Int) {
        viewModelScope.launch {
            when (val result = deleteTaskUseCase(taskId)) {
                is NetworkResult.Success -> {
                    loadTasks()
                }
                is NetworkResult.Error -> {
                    _state.update { it.copy(errorMessage = result.message) }
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun createTask(title: String, description: String?, priority: TaskPriority, dueDate: String? = null) {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, errorMessage = null) }
            when (val result = createTaskUseCase(title, description, dueDate, priority)) {
                is NetworkResult.Success -> {
                    _state.update { it.copy(isCreateDialogOpen = false) }
                    loadTasks()
                }
                is NetworkResult.Error -> {
                    _state.update { it.copy(isLoading = false, errorMessage = result.message) }
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun setCreateDialogOpen(open: Boolean) {
        _state.update { it.copy(isCreateDialogOpen = open) }
    }

    fun clearError() {
        _state.update { it.copy(errorMessage = null) }
    }
}
