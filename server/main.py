import asyncio
import tempfile
import logging
import json
import os
from typing import Optional
from aiogram.types import BufferedInputFile, InputMediaAudio, InputMediaDocument
from aiogram.exceptions import TelegramNetworkError
from fastapi import FastAPI, Path, File, UploadFile, Form, HTTPException
from main import bot
from core import (
    create_manager_sheet,
    setup_google_sheets,
    get_telegram_id_by_company_id,
    find_company_sheet_by_tgid,
    write_call_data_to_manager_sheet
)
from server.repository import format_message_for_bot
from server.shemas import TranscriptionData

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Call Analyzer")

def ms_to_seconds(ms: int) -> float:
    """Преобразует миллисекунды в секунды."""
    return ms / 1000

def calculate_total_call_duration(role_analysis: list) -> float:
    """Рассчитывает общее время звонка."""
    return ms_to_seconds(sum(role.end_time - role.start_time for role in role_analysis))

async def save_temp_file(content: bytes, prefix: str, suffix: str) -> str:
    """Создает временный файл и возвращает путь к нему."""
    try:
        with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            return tmp.name
    except Exception as e:
        logger.error(f"Ошибка при создании временного файла: {e}")
        raise

async def cleanup_temp_files(*file_paths: Optional[str]):
    """Удаляет временные файлы."""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла {path}: {e}")

@app.post("/transcribe/{company_id}")
async def transcribe(
    company_id: int = Path(..., description="ID компании", gt=0),
    data: str = Form(..., description="Данные транскрипции в формате JSON"),
    audio_file: UploadFile = File(..., description="Аудиофайл звонка"),
    manager: str = Form(..., description="Имя менеджера", min_length=2)
):
    """Обрабатывает данные звонка и отправляет результаты в Telegram."""
    logger.info(f"Начата обработка звонка для компании ID: {company_id}, менеджер: {manager}")
    
    temp_file_path = None
    audio_path = None
    sent_messages = []  # Для хранения отправленных сообщений (на случай отката)

    try:
        # Валидация и обработка входных данных
        await audio_file.seek(0)
        audio_content = await audio_file.read()
        logger.info(f"Получен аудиофайл '{audio_file.filename}' размером {len(audio_content)} байт")

        # Парсинг JSON данных
        try:
            data_dict = json.loads(data)
            logger.debug(f"Получены данные транскрипции: {json.dumps(data_dict, indent=2, ensure_ascii=False)}")
            
            # Преобразование данных для соответствия схеме
            if 'lead_qualification' in data_dict and isinstance(data_dict['lead_qualification'], dict):
                data_dict['lead_qualification']['qualified'] = data_dict['lead_qualification'].get('qualified', 'нет')
            
            transcription_data = TranscriptionData(**data_dict)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail="Неверный формат JSON данных")
        except Exception as e:
            logger.error(f"Ошибка валидации: {str(e)}")
            raise HTTPException(status_code=422, detail=f"Ошибка валидации данных: {str(e)}")

        # Получение Telegram ID
        try:
            sheet = setup_google_sheets()
            telegram_id = get_telegram_id_by_company_id(sheet, company_id)
            if not telegram_id:
                raise HTTPException(status_code=404, detail="Telegram ID не найден")
        except Exception as e:
            logger.error(f"Ошибка при работе с Google Sheets: {e}")
            raise HTTPException(status_code=500, detail="Ошибка при работе с таблицами")

        # Расчет длительности звонка
        total_duration = sum((role.end_time - role.start_time) for role in transcription_data.role_analysis) / 1000

        # Работа с таблицей компании
        company_sheet_url = find_company_sheet_by_tgid(telegram_id)
        if not company_sheet_url:
            raise HTTPException(status_code=404, detail="Таблица компании не найдена")

        # Подготовка данных для записи
        is_qualified = transcription_data.lead_qualification.qualified in ('да', True)
        
        write_call_data_to_manager_sheet(
            company_sheet_url,
            manager,
            data_dict,
            total_duration
        )

        # Создание HTML транскрипции
        html_content = [
            f"<p>Менеджер: {manager}</p>"
        ]

        for role in transcription_data.role_analysis:
            start = role.start_time / 1000
            end = role.end_time / 1000
            html_content.extend([
                f"<hr><b>👤 {role.role}:</b>",
                f"<p>🗣️ Текст: {role.text}</p>",
            ])

        temp_file_path = await save_temp_file(
            "\n".join(html_content).encode('utf-8-sig'),
            f"transcript_{company_id}_",
            ".html"
        )

        # Сохранение аудиофайла
        audio_path = await save_temp_file(
            audio_content,
            f"audio_{company_id}_",
            os.path.splitext(audio_file.filename)[1]
        )

        # Отправка файлов в Telegram с обработкой ошибок и повторными попытками
        max_retries = 3
        retry_delay = 2  # секунды

        async def send_with_retry(send_func, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    result = await send_func(*args, **kwargs)
                    sent_messages.append(result)  # Сохраняем отправленное сообщение
                    return result
                except (TelegramNetworkError, TimeoutError) as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Попытка {attempt + 1} из {max_retries} не удалась. Ошибка: {e}")
                    await asyncio.sleep(retry_delay * (attempt + 1))

        try:
            # 1. Сначала отправляем аудиофайл
            await send_with_retry(
                bot.send_audio,
                chat_id=telegram_id,
                audio=BufferedInputFile(audio_content, audio_file.filename),
            )

            # 2. Затем отправляем транскрипцию как документ
            with open(temp_file_path, 'rb') as f:
                transcript_content = f.read()
                await send_with_retry(
                    bot.send_document,
                    chat_id=telegram_id,
                    document=BufferedInputFile(transcript_content, "Транскрипция.html"),
                )

            # 3. Отправляем анализ отдельным сообщением
            message = format_message_for_bot(transcription_data, manager)
            await send_with_retry(
                bot.send_message,
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщений в Telegram: {e}")
            
            # Пытаемся удалить отправленные сообщения при ошибке
            for msg in sent_messages:
                try:
                    await bot.delete_message(chat_id=telegram_id, message_id=msg.message_id)
                except Exception as delete_error:
                    logger.error(f"Не удалось удалить сообщение {msg.message_id}: {delete_error}")
            
            raise HTTPException(status_code=500, detail="Ошибка при отправке данных в Telegram")

        return {
            "company_id": company_id,
            "status": "success",
            "manager": manager,
            "is_qualified": is_qualified,
            "call_duration": total_duration
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Критическая ошибка при обработке звонка: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    finally:
        await cleanup_temp_files(temp_file_path, audio_path)