package com.aman.ai_assistant_frontend.domain.model

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val sender: MessageSender,
    val text: String,
    val timestamp: Long = System.currentTimeMillis(),
    val intent: String? = null
)

enum class MessageSender {
    USER,
    ASSISTANT
}
