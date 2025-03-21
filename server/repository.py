from server.shemas import TranscriptionData

def format_message_for_bot(data: TranscriptionData, manager: str) -> str:
    """
    Форматирует данные для отправки в Telegram (анализ лида и итоговый вердикт).
    """
    message = "📄 *Анализ лида и итоговый вердикт*\n\n"
    
    # Добавляем информацию о менеджере
    message += f"👤 *Менеджер:* {manager}\n\n"
    
    # Добавляем общее время звонка
    total_duration = sum((role.end_time - role.start_time) for role in data.role_analysis) / 1000
    message += f"⏱️ *Общее время звонка:* {total_duration:.2f} секунд\n\n"
    
    # Добавляем анализ лида
    message += "🔹 *Анализ лида:*\n"
    for stage, analysis in data.lead_analysis.stages.items():
        message += (
            f"📌 *Этап {stage.capitalize()}*\n"
            f"✅ *Квалифицирован:* {'Да' if analysis.qualified else 'Нет'}\n"
            f"📝 *Причина:* {analysis.reason}\n"
            f"💡 *Рекомендация:* {analysis.recommendation if analysis.recommendation else 'Нет рекомендации'}\n\n"
        )
    
    # Добавляем итоговый вердикт и процент квалификации
    message += (
        f"🔹 *Итоговый вердикт:* {data.lead_analysis.final_verdict}\n"
        f"📝 *Причина:* {data.lead_analysis.final_reason}\n"
        f"📋 *Полное объяснение:* {data.lead_analysis.final_full_reason}\n"
        f"📊 *Процент квалификации:* {data.lead_analysis.kval_percentage}%\n\n"
    )
    
    # Добавляем анализ слов-паразитов
    message += (
        f"🔹 *Анализ слов-паразитов:*\n"
        f"{data.parasite_words_analysis}\n"
    )
    
    return message