import asyncio
import tempfile
import logging
import json
import os
from aiogram.types import BufferedInputFile
from fastapi import FastAPI, Path, File, UploadFile, Form
from main import bot
from core import create_manager_sheet, setup_google_sheets, get_telegram_id_by_company_id, find_company_sheet_by_tgid, write_call_data_to_manager_sheet
from server.repository import format_message_for_bot
from server.shemas import TranscriptionData

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart"
)

def ms_to_seconds(ms: int) -> float:
    """Преобразует миллисекунды в секунды."""
    return ms / 1000

def calculate_total_call_duration(role_analysis: list) -> float:
    """Рассчитывает общее время звонка."""
    total_duration = 0
    for role in role_analysis:
        total_duration += role.end_time - role.start_time
    return ms_to_seconds(total_duration)

@app.post("/transcribe/{id}")
async def transcribe(
    id: int = Path(..., description="ID компании"),  # ID компании
    data: str = Form(..., description="Данные транскрипции и анализа в формате JSON"),  # JSON данные как строка
    audio_file: UploadFile = File(..., description="Аудиофайл"),  # Аудиофайл
    manager: str = Form(..., description="Имя менеджера")  # Имя менеджера
):
    logger.info(f"Получены данные для компании с ID: {id}.")
    try:
        # Парсим JSON-данные
        data_dict = json.loads(data)
        transcription_data = TranscriptionData(**data_dict)

        # Ищем Telegram ID по ID компании
        sheet = setup_google_sheets()
        telegram_id = get_telegram_id_by_company_id(sheet, id)

        if not telegram_id:
            logger.error(f"Telegram ID для компании с ID {id} не найден.")
            return {"error": "Telegram ID не найден"}

        # Рассчитываем общее время звонка
        total_duration = calculate_total_call_duration(transcription_data.role_analysis)

        # Получаем URL таблицы компании
        company_sheet_url = find_company_sheet_by_tgid(telegram_id)
        
        if not company_sheet_url:
            logger.error(f"Таблица компании для Telegram ID {telegram_id} не найдена.")
            return {"error": "Таблица компании не найдена"}

        # Создаем шапку таблицы, если она еще не создана
        create_manager_sheet(company_sheet_url, manager)

        # Записываем данные в лист менеджера
        is_qualified = transcription_data.lead_analysis.final_verdict == "квалифицированный"
        kval_percentage = transcription_data.lead_analysis.kval_percentage
        parasite_words = transcription_data.parasite_words_analysis
        write_call_data_to_manager_sheet(company_sheet_url, manager, total_duration, is_qualified, kval_percentage, parasite_words)

        # Если диалог неквалифицированный, отправляем данные в Telegram
        if not is_qualified:
            # Создаем временный файл для транскрипции (чистый текст, без HTML)
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write('\ufeff')  # Добавляем BOM
                # Записываем транскрипцию в файл
                temp_file.write(f"<h2>Общее время звонка: {total_duration:.2f} секунд</h2>\n\n")
                temp_file.write(f"Менеджер: {manager}")
                for role in transcription_data.role_analysis:
                    start_time = ms_to_seconds(role.start_time)
                    end_time = ms_to_seconds(role.end_time)
                    temp_file.write(f"<br>👤 {role.role}:</br>")
                    temp_file.write(f"🗣️ Текст: {role.text}\n")
                    temp_file.write(f"<br>⏱️ Время: {start_time:.2f} - {end_time:.2f} секунд\n\n</br>")
                    temp_file.write("<hr></hr>")
                temp_file_path = temp_file.name

            # Читаем содержимое файла и создаем BufferedInputFile
            with open(temp_file_path, 'rb') as file:
                file_content = file.read()
                input_file = BufferedInputFile(file_content, filename="Транскрипция.html")

            # Сохраняем аудиофайл временно
            audio_path = f"temp_audio_{id}.mp3"
            with open(audio_path, "wb") as buffer:
                buffer.write(await audio_file.read())

            # Читаем содержимое аудиофайла и создаем BufferedInputFile
            with open(audio_path, 'rb') as audio:
                audio_content = audio.read()
                input_audio = BufferedInputFile(audio_content, filename=audio_file.filename)

            # Отправляем аудиофайл
            await bot.send_audio(chat_id=telegram_id, audio=input_audio)

            # Небольшая задержка перед отправкой документа
            await asyncio.sleep(1)

            # Отправляем документ с транскрипцией
            await bot.send_document(chat_id=telegram_id, document=input_file)

            # Форматируем остальные данные для отправки в Telegram (в формате HTML)
            message = format_message_for_bot(transcription_data, manager)  # Передаем менеджера в функцию

            # Отправляем сообщение с анализом лида и итоговым вердиктом в формате HTML
            await bot.send_message(chat_id=telegram_id, text=message, parse_mode="HTML")

        return {
            "id_company": id,
            "status": "success",
            "message": "Данные успешно обработаны.",
            "manager": manager,  # Возвращаем имя менеджера в ответе
            "is_qualified": is_qualified,  # Возвращаем статус квалификации
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке данных: {e}")
        return {"error": str(e)}
    finally:
        # Удаляем временные файлы после отправки
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла транскрипции: {e}")
        if 'audio_path' in locals():
            try:
                os.unlink(audio_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного аудиофайла: {e}")