package com.aman.ai_assistant_frontend.presentation.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.CheckCircleOutline
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.aman.ai_assistant_frontend.presentation.navigation.Screen

@Composable
fun AppBottomBar(
    navController: NavController,
    currentRoute: String?
) {
    NavigationBar(
        modifier = Modifier.fillMaxWidth(),
        containerColor = MaterialTheme.colorScheme.surface,
        tonalElevation = 6.dp
    ) {
        val isTasksSelected = currentRoute == Screen.Tasks.route
        NavigationBarItem(
            icon = {
                Icon(
                    imageVector = if (isTasksSelected) Icons.Rounded.CheckCircle else Icons.Outlined.CheckCircleOutline,
                    contentDescription = "Tasks"
                )
            },
            label = {
                Text(
                    "Tasks",
                    fontWeight = if (isTasksSelected) FontWeight.Bold else FontWeight.Medium
                )
            },
            selected = isTasksSelected,
            onClick = {
                if (!isTasksSelected) {
                    navController.navigate(Screen.Tasks.route) {
                        popUpTo(Screen.Tasks.route) { inclusive = true }
                    }
                }
            },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = MaterialTheme.colorScheme.primary,
                selectedTextColor = MaterialTheme.colorScheme.primary,
                indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
            )
        )

        val isChatSelected = currentRoute == Screen.Chat.route
        NavigationBarItem(
            icon = {
                Icon(
                    imageVector = if (isChatSelected) Icons.Rounded.AutoAwesome else Icons.Outlined.AutoAwesome,
                    contentDescription = "AI Assistant"
                )
            },
            label = {
                Text(
                    "AI Assistant",
                    fontWeight = if (isChatSelected) FontWeight.Bold else FontWeight.Medium
                )
            },
            selected = isChatSelected,
            onClick = {
                if (!isChatSelected) {
                    navController.navigate(Screen.Chat.route) {
                        popUpTo(Screen.Tasks.route)
                    }
                }
            },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = MaterialTheme.colorScheme.primary,
                selectedTextColor = MaterialTheme.colorScheme.primary,
                indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
            )
        )
    }
}

