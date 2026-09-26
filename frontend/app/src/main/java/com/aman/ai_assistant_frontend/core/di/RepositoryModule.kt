package com.aman.ai_assistant_frontend.core.di

import com.aman.ai_assistant_frontend.data.repository.AuthRepositoryImpl
import com.aman.ai_assistant_frontend.data.repository.ChatRepositoryImpl
import com.aman.ai_assistant_frontend.data.repository.TaskRepositoryImpl
import com.aman.ai_assistant_frontend.domain.repository.AuthRepository
import com.aman.ai_assistant_frontend.domain.repository.ChatRepository
import com.aman.ai_assistant_frontend.domain.repository.TaskRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        impl: AuthRepositoryImpl
    ): AuthRepository

    @Binds
    @Singleton
    abstract fun bindTaskRepository(
        impl: TaskRepositoryImpl
    ): TaskRepository

    @Binds
    @Singleton
    abstract fun bindChatRepository(
        impl: ChatRepositoryImpl
    ): ChatRepository
}
