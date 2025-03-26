from server.shemas import TranscriptionData

def format_message_for_bot(data: TranscriptionData, manager: str) -> str:
    """
    Форматирует данные для отправки в Telegram согласно требованиям.
    """
    message = "<b>📊 Полный анализ звонка</b>\n\n"
    message += f"👤 <b>Менеджер:</b> {manager}\n\n"
    
    # 1. Общая оценка менеджера
    message += f"1️⃣ <b>Общая оценка менеджера:</b> {data.manager_evaluation.score}%\n"
    message += f"<i>{data.manager_evaluation.explanation}</i>\n\n"
    
    # Детали оценки (переведены на русский)
    aspect_translations = {
        "dialog_quality": "Качество диалога",
        "logic_adherence": "Соблюдение логики",
        "confidence": "Уверенность",
        "additional_aspects": "Дополнительные аспекты"
    }
    
    for aspect, detail in data.manager_evaluation.details.items():
        translated_aspect = aspect_translations.get(aspect, aspect)
        message += f"<b>{translated_aspect}:</b> {detail.score}%\n"
        message += f"<i>{detail.reason}</i>\n\n"

    # 2. Список ошибок менеджера
    message += "2️⃣ <b>Список ошибок менеджера:</b>\n"
    if data.manager_errors:
        for error in data.manager_errors:
            message += f"• {error}\n"
    else:
        message += "Нет значительных ошибок\n"
    message += "\n"

    # 3. Итог диалога
    message += f"3️⃣ <b>Итог диалога:</b>\n{data.dialogue_outcomes}\n\n"

    # 4. Оценка квалификации лида
    qualified = "Да" if data.lead_qualification.qualified == "да" else "Нет"
    message += f"4️⃣ <b>Квалификация лида:</b> {qualified}\n"
    if data.lead_lost:
        message += f"<i>Статус лида:</i> {data.lead_lost}\n"
    message += "\n"

    # 5. Оценка отработки возражений
    message += f"5️⃣ <b>Отработка возражений:</b> {data.objection_handling.evaluation}\n"
    message += f"<i>Возражения присутствовали:</i> {'Да' if data.objection_handling.has_objections else 'Нет'}\n\n"

    # 6. Оценка готовности клиента
    readiness_map = {
        "Не интересно": "🔴 Не интересно",
        "Слабый интерес": "🟡 Слабый интерес", 
        "Сильный интерес": "🟢 Сильный интерес"
    }
    readiness = readiness_map.get(data.client_readiness.level, data.client_readiness.level)
    message += f"6️⃣ <b>Готовность клиента:</b> {readiness}\n"
    message += f"<i>Пояснение:</i> {data.client_readiness.explanation}\n\n"

    # 7. Уровень уверенности менеджера
    confidence = "🟢 Уверен" if "уверен" in data.manager_confidence.confidence.lower() else "🔴 Не уверен"
    message += f"7️⃣ <b>Уверенность менеджера:</b> {confidence}\n"
    if data.manager_confidence.criteria:
        message += "<i>Критерии:</i>\n"
        for criterion in data.manager_confidence.criteria:
            message += f"• {criterion}\n"
    message += "\n"

    # 8. Уровень экспертизы в продукте
    expertise = data.product_expertise.level
    message += f"8️⃣ <b>Экспертиза в продукте:</b> {expertise}\n"
    message += f"<i>N/A:</i> {'Да' if data.product_expertise.is_na else 'Нет'}\n\n"

    # 9. Рекомендации для менеджера
    message += "9️⃣ <b>Рекомендации:</b>\n"
    if hasattr(data, 'recommendations') and data.recommendations:
        for recommendation in data.recommendations:
            if isinstance(recommendation, dict):
                error = recommendation.get('error', {})
            else:
                error = getattr(recommendation, 'error', {})
            
            if isinstance(error, dict):
                quote = error.get('quote')
                analysis = error.get('analysis')
                advice = error.get('advice')
            else:
                quote = getattr(error, 'quote', None)
                analysis = getattr(error, 'analysis', None)
                advice = getattr(error, 'advice', None)
            
            if quote:
                message += f"<b>Цитата:</b> {quote}\n"
            if analysis:
                message += f"<b>Анализ:</b> {analysis}\n"
            if advice:
                message += f"<b>Совет:</b> {advice}\n"
            
            message += "---\n"
    else:
        message += "Нет конкретных рекомендаций\n"
    
    return message