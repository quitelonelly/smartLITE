from server.shemas import TranscriptionData

def format_message_for_bot(data: TranscriptionData) -> str:
    """
    Форматирует данные для отправки в Telegram.
    """
    message = "📄 *Транскрипция и анализ звонка*\n\n"
    
    # Добавляем анализ ролей
    message += "🔹 *Транскрипция звонка:*\n"
    for role in data.role_analysis:
        message += (
            f"👤 *{role.role} ({role.speaker}):*\n"
            f"🗣️ *Текст:* {role.text}\n"
            f"⏱️ *Время:* {role.start_time} - {role.end_time} мс\n\n"
        )
    
    # Добавляем анализ лида
    message += "🔹 *Анализ лида:*\n"
    for stage, analysis in data.lead_analysis.stages.items():
        message += (
            f"📌 *Этап {stage.capitalize()}*\n"
            f"✅ *Квалифицирован:* {'Да' if analysis.qualified else 'Нет'}\n"
            f"📝 *Причина:* {analysis.reason}\n"
            f"💡 *Рекомендация:* {analysis.recommendation}\n\n"
        )
    
    # Добавляем итоговый вердикт
    message += (
        f"🔹 *Итоговый вердикт:* {data.lead_analysis.final_verdict}\n"
        f"📝 *Причина:* {data.lead_analysis.final_reason}\n"
    )
    
    return message