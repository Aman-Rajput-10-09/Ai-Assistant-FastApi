package com.aman.ai_assistant_frontend.domain.repository

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.ChatMessage

interface ChatRepository {
    suspend fun sendMessage(messageText: String): NetworkResult<ChatMessage>
}
