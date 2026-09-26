package com.aman.ai_assistant_frontend.presentation.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.ChatMessage
import com.aman.ai_assistant_frontend.domain.model.MessageSender
import com.aman.ai_assistant_frontend.domain.usecase.chat.SendChatMessageUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val sendChatMessageUseCase: SendChatMessageUseCase
) : ViewModel() {

    private val _state = MutableStateFlow(
        ChatState(
            messages = listOf(
                ChatMessage(
                    sender = MessageSender.ASSISTANT,
                    text = "Hello! I am your AI Scheduling Assistant. Ask me to schedule tasks, manage your agenda, or check your productivity stats!"
                )
            )
        )
    )
    val state: StateFlow<ChatState> = _state.asStateFlow()

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        val userMessage = ChatMessage(
            sender = MessageSender.USER,
            text = text.trim()
        )

        _state.update {
            it.copy(
                messages = it.messages + userMessage,
                isLoading = true,
                errorMessage = null
            )
        }

        viewModelScope.launch {
            when (val result = sendChatMessageUseCase(text)) {
                is NetworkResult.Success -> {
                    _state.update {
                        it.copy(
                            isLoading = false,
                            messages = it.messages + result.data
                        )
                    }
                }
                is NetworkResult.Error -> {
                    _state.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = result.message
                        )
                    }
                }
                is NetworkResult.Loading -> {
                    _state.update { it.copy(isLoading = true) }
                }
            }
        }
    }

    fun clearError() {
        _state.update { it.copy(errorMessage = null) }
    }
}
