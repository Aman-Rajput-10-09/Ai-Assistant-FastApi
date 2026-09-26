package com.aman.ai_assistant_frontend.domain.usecase.auth

import com.aman.ai_assistant_frontend.domain.repository.AuthRepository
import javax.inject.Inject

class IsUserLoggedInUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    operator fun invoke(): Boolean = authRepository.isLoggedIn()
}
