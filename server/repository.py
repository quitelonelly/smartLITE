from server.shemas import TranscriptionData

def format_message_for_bot(data: TranscriptionData) -> str:
    """
    Форматирует данные для отправки в Telegram (анализ лида и итоговый вердикт).
    """
    message = "📄 *Анализ лида и итоговый вердикт*\n\n"
    
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