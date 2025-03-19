from fastapi import FastAPI, Path, Body
from handlers import setup_google_sheets, get_telegram_id_by_company_id
from server.repository import format_message_for_bot
from server.shemas import TranscriptionData
from main import bot  # Импортируем бота
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart"
)

@app.post("/transcribe/{id}")
async def transcribe(
    id: int = Path(..., description="ID компании"),  # ID компании
    data: TranscriptionData = Body(..., description="Данные транскрипции и анализа")  # JSON данные
):
    logger.info(f"Получены данные для компании с ID: {id}.")
    try:
        # Ищем Telegram ID по ID компании
        sheet = setup_google_sheets()
        telegram_id = get_telegram_id_by_company_id(sheet, id)

        if not telegram_id:
            logger.error(f"Telegram ID для компании с ID {id} не найден.")
            return {"error": "Telegram ID не найден"}

        # Форматируем данные для отправки в Telegram
        message = format_message_for_bot(data)

        # Отправляем сообщение в Telegram
        await bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")

        return {
            "id_company": id,
            "status": "success",
            "message": "Данные успешно отправлены в Telegram."
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке данных: {e}")
        return {"error": str(e)}    