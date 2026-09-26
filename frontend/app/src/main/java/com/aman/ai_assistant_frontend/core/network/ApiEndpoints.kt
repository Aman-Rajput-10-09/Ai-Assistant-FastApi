package com.aman.ai_assistant_frontend.core.network

object ApiEndpoints {
    // Your Mac's local network IP (accessible by physical Android phones and emulators)
    const val BASE_URL = "http://10.240.192.153:8000/api/v1/"
    
    // Auth endpoints
    const val LOGIN = "auth/login"
    const val REGISTER = "auth/register"
    const val REFRESH = "auth/refresh"
    const val LOGOUT = "auth/logout"
    
    // Tasks endpoints
    const val TASKS = "tasks"
    
    // Chat endpoint
    const val CHAT = "chat"
}
