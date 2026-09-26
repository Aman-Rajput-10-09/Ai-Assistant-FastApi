package com.aman.ai_assistant_frontend.domain.usecase.chat

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.ChatMessage
import com.aman.ai_assistant_frontend.domain.repository.ChatRepository
import javax.inject.Inject

class SendChatMessageUseCase @Inject constructor(
    private val chatRepository: ChatRepository
) {
    suspend operator fun invoke(messageText: String): NetworkResult<ChatMessage> {
        if (messageText.isBlank()) {
            return NetworkResult.Error("Message cannot be empty")
        }
        return chatRepository.sendMessage(messageText.trim())
    }
}
