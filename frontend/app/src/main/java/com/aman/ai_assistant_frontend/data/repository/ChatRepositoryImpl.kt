package com.aman.ai_assistant_frontend.data.repository

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.data.model.ChatRequestDto
import com.aman.ai_assistant_frontend.data.remote.ChatApiService
import com.aman.ai_assistant_frontend.domain.model.ChatMessage
import com.aman.ai_assistant_frontend.domain.model.MessageSender
import com.aman.ai_assistant_frontend.domain.repository.ChatRepository
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepositoryImpl @Inject constructor(
    private val chatApiService: ChatApiService
) : ChatRepository {

    override suspend fun sendMessage(messageText: String): NetworkResult<ChatMessage> {
        return try {
            val response = chatApiService.sendMessage(ChatRequestDto(message = messageText))
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val assistantMessage = ChatMessage(
                    sender = MessageSender.ASSISTANT,
                    text = body.reply,
                    intent = body.intent
                )
                NetworkResult.Success(assistantMessage)
            } else {
                NetworkResult.Error(response.errorBody()?.string() ?: "Failed to get AI response", response.code())
            }
        } catch (e: Exception) {
            NetworkResult.Error(e.localizedMessage ?: "Failed to connect to AI Assistant")
        }
    }
}
