package com.aman.ai_assistant_frontend.presentation.chat

import com.aman.ai_assistant_frontend.domain.model.ChatMessage

data class ChatState(
    val isLoading: Boolean = false,
    val messages: List<ChatMessage> = emptyList(),
    val errorMessage: String? = null
)
