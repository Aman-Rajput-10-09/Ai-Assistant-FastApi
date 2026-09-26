package com.aman.ai_assistant_frontend.presentation.navigation

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Register : Screen("register")
    data object Tasks : Screen("tasks")
    data object Chat : Screen("chat")
}
