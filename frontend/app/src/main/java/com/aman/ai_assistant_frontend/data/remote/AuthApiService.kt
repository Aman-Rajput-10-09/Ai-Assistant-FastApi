package com.aman.ai_assistant_frontend.data.remote

import com.aman.ai_assistant_frontend.core.network.ApiEndpoints
import com.aman.ai_assistant_frontend.data.model.LoginRequestDto
import com.aman.ai_assistant_frontend.data.model.RefreshTokenRequestDto
import com.aman.ai_assistant_frontend.data.model.RegisterRequestDto
import com.aman.ai_assistant_frontend.data.model.TokenResponseDto
import com.aman.ai_assistant_frontend.data.model.UserDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApiService {

    @POST(ApiEndpoints.LOGIN)
    suspend fun login(@Body request: LoginRequestDto): Response<TokenResponseDto>

    @POST(ApiEndpoints.REGISTER)
    suspend fun register(@Body request: RegisterRequestDto): Response<UserDto>

    @POST(ApiEndpoints.REFRESH)
    suspend fun refresh(@Body request: RefreshTokenRequestDto): Response<TokenResponseDto>

    @POST(ApiEndpoints.LOGOUT)
    suspend fun logout(@Body request: RefreshTokenRequestDto): Response<Map<String, String>>
}
