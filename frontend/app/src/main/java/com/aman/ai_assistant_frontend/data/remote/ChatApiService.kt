package com.aman.ai_assistant_frontend.data.remote

import com.aman.ai_assistant_frontend.core.network.ApiEndpoints
import com.aman.ai_assistant_frontend.data.model.ChatRequestDto
import com.aman.ai_assistant_frontend.data.model.ChatResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface ChatApiService {

    @POST(ApiEndpoints.CHAT)
    suspend fun sendMessage(
        @Body request: ChatRequestDto
    ): Response<ChatResponseDto>
}
