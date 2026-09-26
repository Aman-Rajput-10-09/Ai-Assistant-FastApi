package com.aman.ai_assistant_frontend.data.model

import com.google.gson.annotations.SerializedName

data class ChatRequestDto(
    @SerializedName("message") val message: String
)

data class ChatResponseDto(
    @SerializedName("intent") val intent: String,
    @SerializedName("reply") val reply: String,
    @SerializedName("should_schedule_alarm") val shouldScheduleAlarm: Boolean? = false,
    @SerializedName("reminder_at") val reminderAt: String? = null
)
