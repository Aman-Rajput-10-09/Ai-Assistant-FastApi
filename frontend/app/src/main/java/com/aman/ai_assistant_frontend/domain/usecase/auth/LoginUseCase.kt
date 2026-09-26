package com.aman.ai_assistant_frontend.domain.usecase.auth

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.repository.AuthRepository
import javax.inject.Inject

class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String): NetworkResult<Boolean> {
        if (email.isBlank()) return NetworkResult.Error("Email cannot be empty")
        if (password.isBlank()) return NetworkResult.Error("Password cannot be empty")
        return authRepository.login(email, password)
    }
}
