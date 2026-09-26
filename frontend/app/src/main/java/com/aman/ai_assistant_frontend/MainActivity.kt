package com.aman.ai_assistant_frontend

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.aman.ai_assistant_frontend.presentation.navigation.AppNavigation
import com.aman.ai_assistant_frontend.ui.theme.AiassistantfrontendTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AiassistantfrontendTheme {
                AppNavigation()
            }
        }
    }
}