package com.aman.ai_assistant_frontend.presentation.navigation

import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.isImeVisible
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.aman.ai_assistant_frontend.presentation.auth.AuthViewModel
import com.aman.ai_assistant_frontend.presentation.auth.LoginScreen
import com.aman.ai_assistant_frontend.presentation.auth.RegisterScreen
import com.aman.ai_assistant_frontend.presentation.chat.ChatScreen
import com.aman.ai_assistant_frontend.presentation.chat.ChatViewModel
import com.aman.ai_assistant_frontend.presentation.components.AppBottomBar
import com.aman.ai_assistant_frontend.presentation.tasks.TasksScreen
import com.aman.ai_assistant_frontend.presentation.tasks.TasksViewModel

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AppNavigation(
    authViewModel: AuthViewModel = hiltViewModel()
) {
    val navController = rememberNavController()
    val authState by authViewModel.state.collectAsState()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    // React to authentication state changes
    LaunchedEffect(authState.isAuthenticated) {
        if (authState.isAuthenticated) {
            if (currentRoute == Screen.Login.route || currentRoute == Screen.Register.route || currentRoute == null) {
                navController.navigate(Screen.Tasks.route) {
                    popUpTo(0) { inclusive = true }
                }
            }
        } else {
            if (currentRoute != Screen.Login.route && currentRoute != Screen.Register.route) {
                navController.navigate(Screen.Login.route) {
                    popUpTo(0) { inclusive = true }
                }
            }
        }
    }

    val isKeyboardVisible = WindowInsets.isImeVisible
    val showBottomBar = currentRoute in listOf(Screen.Tasks.route, Screen.Chat.route) && !isKeyboardVisible

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        bottomBar = {
            if (showBottomBar) {
                AppBottomBar(
                    navController = navController,
                    currentRoute = currentRoute
                )
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = if (authState.isAuthenticated) Screen.Tasks.route else Screen.Login.route,
            modifier = Modifier.padding(bottom = innerPadding.calculateBottomPadding())
        ) {
            composable(Screen.Login.route) {
                LoginScreen(
                    state = authState,
                    onLoginClick = { email, pass -> authViewModel.login(email, pass) },
                    onNavigateToRegister = { navController.navigate(Screen.Register.route) }
                )
            }

            composable(Screen.Register.route) {
                RegisterScreen(
                    state = authState,
                    onRegisterClick = { email, pass, name -> authViewModel.register(email, pass, name) },
                    onNavigateToLogin = { navController.navigate(Screen.Login.route) }
                )
            }

            composable(Screen.Tasks.route) {
                val tasksViewModel: TasksViewModel = hiltViewModel()
                val tasksState by tasksViewModel.state.collectAsState()

                TasksScreen(
                    state = tasksState,
                    onTabSelected = { tasksViewModel.selectTab(it) },
                    onToggleTask = { tasksViewModel.toggleTask(it) },
                    onDeleteTask = { tasksViewModel.deleteTask(it) },
                    onCreateTask = { title, desc, priority, dueDate ->
                        tasksViewModel.createTask(title, desc, priority, dueDate)
                    },
                    onOpenCreateDialog = { tasksViewModel.setCreateDialogOpen(it) },
                    onLogoutClick = { authViewModel.logout() }
                )
            }

            composable(Screen.Chat.route) {
                val chatViewModel: ChatViewModel = hiltViewModel()
                val chatState by chatViewModel.state.collectAsState()

                ChatScreen(
                    state = chatState,
                    onSendMessage = { chatViewModel.sendMessage(it) },
                    onLogoutClick = { authViewModel.logout() }
                )
            }
        }
    }
}
