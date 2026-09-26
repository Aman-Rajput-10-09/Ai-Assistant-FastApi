package com.aman.ai_assistant_frontend.domain.repository

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.User

interface AuthRepository {
    suspend fun login(email: String, password: String): NetworkResult<Boolean>
    suspend fun register(email: String, password: String, fullName: String): NetworkResult<User>
    suspend fun logout(): NetworkResult<Unit>
    fun isLoggedIn(): Boolean
}
