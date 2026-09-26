package com.aman.ai_assistant_frontend.domain.usecase.auth

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.domain.model.User
import com.aman.ai_assistant_frontend.domain.repository.AuthRepository
import javax.inject.Inject

class RegisterUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String, fullName: String): NetworkResult<User> {
        if (fullName.isBlank()) return NetworkResult.Error("Name cannot be empty")
        if (email.isBlank()) return NetworkResult.Error("Email cannot be empty")
        if (password.length < 6) return NetworkResult.Error("Password must be at least 6 characters")
        return authRepository.register(email, password, fullName)
    }
}
