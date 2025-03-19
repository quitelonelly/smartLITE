# Импорт необходимых библиотек
import os
import gspread

from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import kb_tran
from states import Form

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_telegram_id_by_company_id(sheet, company_id):
    """
    Ищет Telegram ID по ID компании в Google Sheets.
    """
    try:
        # Получаем все данные из таблицы
        all_values = sheet.get_all_values()
        
        # Ищем строку с нужным ID компании
        for row in all_values:
            if row[0] == str(company_id):  # ID компании в первом столбце
                return row[1]  # Telegram ID во втором столбце
        
        # Если ID компании не найден
        return None
    except Exception as e:
        print(f"Ошибка при поиске Telegram ID: {e}")
        return None

# Настройка Google Sheets API
def setup_google_sheets(sheet_index=0):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "/home/klim-petrov/projects/smartLITE/credentials.json", scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1CoDQJn0T_scUV7ZsbYU8x2nZTzu_F9CBrculeQIG2KA").get_worksheet(sheet_index)
    return sheet

# Функция для получения следующего ID
def get_next_id(sheet):
    try:
        ids = sheet.col_values(1)
        if len(ids) > 1:
            last_id = int(ids[-1])
            return last_id + 1
        else:
            return 1
    except Exception as e:
        print(f"Ошибка при получении ID: {e}")
        return 1

# Функция для обновления листа конверсии
def update_conversion_sheet(sheet, argument, column_name):
    try:
        all_values = sheet.get_all_values()
        
        # Ищем строку с нужным аргументом
        for i, row in enumerate(all_values):
            if row[0] == argument:
                # Находим индекс столбца по его названию
                column_index = all_values[0].index(column_name)
                current_value = int(row[column_index]) if row[column_index] else 0
                sheet.update_cell(i + 1, column_index + 1, current_value + 1)
                return
        
        # Если строка с таким аргументом не найдена, создаем новую
        new_row = [argument] + [0] * (len(all_values[0]) - 1)
        column_index = all_values[0].index(column_name)
        new_row[column_index] = 1
        sheet.append_row(new_row)
    except Exception as e:
        print(f"Ошибка при обновлении листа конверсии: {e}")

# Обработка команды /start с аргументом
async def cmd_start(message: types.Message, command: Command, state: FSMContext):
    args = command.args
    
    if args:
        try:
            await message.answer(
                "Приветствую в LITE версии продукта🥳\nНажмите кнопку и отправьте аудиофайл с диалогом для транскрипции!", 
                parse_mode="HTML", 
                reply_markup=kb_tran
            )

            sheet = setup_google_sheets()
            next_id = get_next_id(sheet)
            sheet.append_row([next_id, message.from_user.id, args])

            conversion_sheet = setup_google_sheets(1)
            update_conversion_sheet(conversion_sheet, args, "start_clicked")

        except Exception as e:
            print(e)
            await message.answer(f"Ошибка при записи в таблицу", parse_mode="HTML")
    else:
        await message.answer("Ты не передал аргумент.", parse_mode="HTML")

# Обработчик кнопки "Отправить файл" (ReplyKeyboard)
async def send_file_handler(message: types.Message, state: FSMContext):
    await message.answer("Загрузите аудиофайл с диалогом для транскрибации.")
    await state.set_state(Form.waiting_for_audio)

# Обработчик аудиофайла
async def process_audio(message: types.Message, state: FSMContext):
    if message.audio:
        await message.answer("Спасибо за загрузку аудиофайла!")
        await state.clear()  # Очищаем состояние
    else:
        await message.answer("Пожалуйста, загрузите аудиофайл.")

# Регистрация всех обработчиков
def reg_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command(commands=['start']))
    dp.message.register(send_file_handler, F.text == 'Отправить файл')  # Обработчик кнопки "Отправить файл"
    dp.message.register(process_audio, Form.waiting_for_audio)  # Обработчик аудиофайла