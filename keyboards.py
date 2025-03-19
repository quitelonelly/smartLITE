from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


kb_tran = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отправить файл")]  # Обычная кнопка ReplyKeyboard
    ],
    resize_keyboard=True
)