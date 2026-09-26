package com.aman.ai_assistant_frontend.data.repository

import com.aman.ai_assistant_frontend.core.network.NetworkResult
import com.aman.ai_assistant_frontend.core.network.TokenManager
import com.aman.ai_assistant_frontend.data.model.LoginRequestDto
import com.aman.ai_assistant_frontend.data.model.RefreshTokenRequestDto
import com.aman.ai_assistant_frontend.data.model.RegisterRequestDto
import com.aman.ai_assistant_frontend.data.remote.AuthApiService
import com.aman.ai_assistant_frontend.domain.model.User
import com.aman.ai_assistant_frontend.domain.repository.AuthRepository
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val authApiService: AuthApiService,
    private val tokenManager: TokenManager
) : AuthRepository {

    override suspend fun login(email: String, password: String): NetworkResult<Boolean> {
        return try {
            val response = authApiService.login(LoginRequestDto(email = email.trim(), password = password))
            if (response.isSuccessful && response.body() != null) {
                val token = response.body()!!
                tokenManager.saveTokens(token.accessToken, token.refreshToken)
                NetworkResult.Success(true)
            } else {
                val errMsg = response.errorBody()?.string() ?: "Invalid email or password"
                NetworkResult.Error(errMsg, response.code())
            }
        } catch (e: Exception) {
            NetworkResult.Error(e.localizedMessage ?: "Network connection error")
        }
    }

    override suspend fun register(email: String, password: String, fullName: String): NetworkResult<User> {
        return try {
            val response = authApiService.register(
                RegisterRequestDto(email = email.trim(), password = password, fullName = fullName.trim())
            )
            if (response.isSuccessful && response.body() != null) {
                val dto = response.body()!!
                NetworkResult.Success(
                    User(id = dto.id, email = dto.email, fullName = dto.fullName ?: "")
                )
            } else {
                val errMsg = response.errorBody()?.string() ?: "Failed to register"
                NetworkResult.Error(errMsg, response.code())
            }
        } catch (e: Exception) {
            NetworkResult.Error(e.localizedMessage ?: "Network connection error")
        }
    }

    override suspend fun logout(): NetworkResult<Unit> {
        val refreshToken = tokenManager.getRefreshToken()
        if (!refreshToken.isNullOrBlank()) {
            try {
                authApiService.logout(RefreshTokenRequestDto(refreshToken))
            } catch (_: Exception) {
                // Ignore network error on logout
            }
        }
        tokenManager.clearTokens()
        return NetworkResult.Success(Unit)
    }

    override fun isLoggedIn(): Boolean = tokenManager.isLoggedIn()
}
