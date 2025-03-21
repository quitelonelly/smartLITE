import os
import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import F, Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import kb_tran
from states import Form
from core import create_new_sheet, get_company_id_by_tgid, get_managers_from_sheet, is_user_registered, setup_google_sheets, update_conversion_sheet, find_company_sheet_by_tgid

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


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



async def cmd_start(message: types.Message, command: Command, state: FSMContext):
    args = command.args
    tgid = message.from_user.id  # Telegram ID пользователя

    # Проверяем, зарегистрирован ли пользователь
    sheet = setup_google_sheets()
    if is_user_registered(sheet, tgid):
        # Если пользователь уже зарегистрирован
        await message.answer("Вы уже зарегистрированы! 😊", parse_mode="HTML", reply_markup=kb_tran)
        return

    if args:
        try:
            await message.answer(
                "Приветствую в LITE версии продукта🥳\nНажмите кнопку и отправьте аудиофайл с диалогом для транскрипции!", 
                parse_mode="HTML", 
                reply_markup=kb_tran
            )

            next_id = get_next_id(sheet)
            
            # Создаем новую таблицу для компании
            new_sheet_url = create_new_sheet(args)
            
            # Записываем данные в существующую таблицу
            sheet.append_row([next_id, tgid, args, new_sheet_url])

            conversion_sheet = setup_google_sheets(1)
            update_conversion_sheet(conversion_sheet, args, "start_clicked")

        except Exception as e:
            print(e)
            await message.answer(f"Ошибка при записи в таблицу", parse_mode="HTML")
    else:
        await message.answer("Ты не передал аргумент.", parse_mode="HTML")

async def cmd_info(message: types.Message):
    """
    Обработчик команды /info.
    Ищет URL таблицы компании по Telegram ID пользователя и отправляет его.
    """
    tgid = message.from_user.id  # Telegram ID пользователя
    
    # Ищем таблицу компании по Telegram ID
    company_sheet_url = find_company_sheet_by_tgid(tgid)
    
    if company_sheet_url:
        await message.answer(f"URL вашей таблицы компании: {company_sheet_url}")
    else:
        await message.answer("Таблица компании не найдена.")

import httpx  # Импортируем библиотеку для HTTP-запросов
from aiogram.types import FSInputFile

async def send_file_handler(message: types.Message, state: FSMContext):
    tgid = message.from_user.id  # Telegram ID пользователя
    
    # Ищем таблицу компании по Telegram ID
    company_sheet_url = find_company_sheet_by_tgid(tgid)
    
    if company_sheet_url:
        # Получаем список менеджеров (листов) из таблицы компании
        managers = get_managers_from_sheet(company_sheet_url)
        
        if managers:
            # Создаем инлайн-клавиатуру с менеджерами
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=manager, callback_data=f"manager_{manager}")] for manager in managers
            ])
            
            # Отправляем сообщение с клавиатурой
            await message.answer("Выберите менеджера:", reply_markup=keyboard)
        else:
            await message.answer("Менеджеры не найдены в таблице компании.")
    else:
        await message.answer("Не удалось найти таблицу компании.")
    
    await state.set_state(Form.waiting_for_manager)  # Устанавливаем состояние ожидания выбора менеджера


async def process_audio(message: types.Message, state: FSMContext):
    if message.audio:
        # Получаем данные из состояния
        data = await state.get_data()
        manager_name = data.get("selected_manager")
        
        if not manager_name:
            await message.answer("Ошибка: менеджер не выбран.")
            return

        # Получаем ID компании из таблицы
        tgid = message.from_user.id
        sheet = setup_google_sheets()
        company_id = get_company_id_by_tgid(sheet, tgid)

        if not company_id:
            await message.answer("Ошибка: ID компании не найден.")
            return

        # Сохраняем аудиофайл временно
        audio_path = f"temp_audio_{company_id}.mp3"
        
        # Скачиваем аудиофайл
        file_id = message.audio.file_id
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=audio_path)

        try:
            # Отправляем запрос на внешний сервер
            async with httpx.AsyncClient() as client:
                with open(audio_path, "rb") as audio_file:
                    files = {"file": (audio_path, audio_file, "audio/mpeg")}
                    data = {"id": company_id, "manager_name": manager_name}
                    response = await client.post(
                        "http://185.207.0.3:5001/analyze",
                        files=files,
                        data=data
                    )

                if response.status_code == 200:
                    await message.answer("Файл успешно отправлен на анализ!")
                else:
                    await message.answer(f"Ошибка при отправке файла: {response.status_code}")
        except Exception as e:
            await message.answer(f"Ошибка при отправке файла: {str(e)}")
        finally:
            # Удаляем временный файл
            if os.path.exists(audio_path):
                os.unlink(audio_path)
        
        # Очищаем состояние
        await state.clear()
    else:
        await message.answer("Пожалуйста, загрузите аудиофайл.")

async def process_manager_selection(callback: types.CallbackQuery, state: FSMContext):
    # Получаем выбранного менеджера из callback_data
    manager_name = callback.data.replace("manager_", "")
    
    # Сохраняем выбранного менеджера в состояние
    await state.update_data(selected_manager=manager_name)
    
    # Отправляем подтверждение
    await callback.message.answer(f"Вы выбрали менеджера: {manager_name}. Теперь отправьте аудиофайл.")
    
    # Устанавливаем состояние ожидания аудиофайла
    await state.set_state(Form.waiting_for_audio)


async def cmd_add_manager(message: types.Message, state: FSMContext):
    await message.answer("Введите имя менеджера:")
    await state.set_state(Form.waiting_for_manager)

async def process_manager_name(message: types.Message, state: FSMContext):
    manager_name = message.text
    tgid = message.from_user.id  # Telegram ID пользователя
    
    # Ищем таблицу компании по Telegram ID
    company_sheet_url = find_company_sheet_by_tgid(tgid)
    
    if company_sheet_url:
        try:
            await message.answer(f"Менеджер {manager_name} успешно добавлен!")
            
            # Открываем таблицу компании
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                "/home/klim-petrov/projects/smartLITE/credentials.json", scope
            )
            client = gspread.authorize(creds)
            company_sheet = client.open_by_url(company_sheet_url)
            
            # Создаем новый лист с именем менеджера
            company_sheet.add_worksheet(title=f"Менеджер {manager_name}", rows="100", cols="20")
            
        except Exception as e:
            print(e)
            await message.answer("Ошибка при создании листа для менеджера.")
    else:
        await message.answer("Не удалось найти таблицу компании.")
    
    await state.clear()

def reg_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command(commands=['start']))
    dp.message.register(send_file_handler, F.text == 'Отправить файл')  # Обработчик кнопки "Отправить файл"
    dp.message.register(process_audio, Form.waiting_for_audio)  # Обработчик аудиофайла
    dp.message.register(cmd_add_manager, Command(commands=['add_manager']))  # Обработчик команды /add_manager
    dp.message.register(process_manager_name, Form.waiting_for_manager)  # Обработчик ввода имени менеджера
    dp.message.register(cmd_info, Command(commands=['info']))  # Обработчик команды /info
    dp.callback_query.register(process_manager_selection, F.data.startswith("manager_"))  # Обработчик выбора менеджера