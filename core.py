import os
from typing import List, Optional
from oauth2client.service_account import ServiceAccountCredentials
import gspread

def is_user_registered(sheet, tgid: int) -> bool:
    """
    Проверяет, зарегистрирован ли пользователь по его telegram_id.
    Возвращает True@app.post("/transcribe/{id}")
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

        # Записываем данные в лист менеджера
        is_qualified = transcription_data.lead_analysis.final_verdict == "Квалифицирован"
        write_call_data_to_manager_sheet(company_sheet_url, manager, f"Время звонка: {total_duration}", is_qualified)

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
            "message": "Данные успешно отправлены в Telegram.",
            "manager": manager  # Возвращаем имя менеджера в ответе
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
                logger.error(f"Ошибка при удалении временного аудиофайла: {e}"), если зарегистрирован, иначе False.
    """
    try:
        # Получаем все данные из таблицы
        records = sheet.get_all_records()
        print(tgid)
        print(f"Records: {records}")  # Логируем данные из таблицы
        
        # Ищем строку с нужным telegram_id (предполагаем, что он во втором столбце)
        for record in records:
            print(f"Record: {record}, tgid: {record.get('tgid')}")  # Логируем каждую запись
            if record.get('tgid') == int(tgid):  # Приводим tgid к строке для сравнения
                return True
        
        # Если telegram_id не найден
        return False
    except Exception as e:
        print(f"Ошибка при проверке регистрации пользователя: {e}")
        return False
    
def setup_google_sheets(sheet_index=0):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "/home/klim-petrov/projects/smartLITE/credentials.json", scope
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1CoDQJn0T_scUV7ZsbYU8x2nZTzu_F9CBrculeQIG2KA").get_worksheet(sheet_index)
        return sheet

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
    
def create_new_sheet(company_name):
    """
    Создает новую таблицу для компании и настраивает доступ.
    Возвращает URL созданной таблицы.
    """
    try:
        # Настройка области доступа и авторизация
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "/home/klim-petrov/projects/smartLITE/credentials.json", scope
        )
        client = gspread.authorize(creds)
        
        # Создаем новую таблицу
        new_sheet = client.create(f"Company_{company_name}")
        
        # Настраиваем доступ по ссылке
        new_sheet.share(None, perm_type='anyone', role='writer')  # Доступ по ссылке с правом редактирования
        
        # Предоставляем доступ сервисному аккаунту
        service_account_email = os.getenv('SERVICE_ACC')  # Email сервисного аккаунта
        new_sheet.share(service_account_email, perm_type='user', role='writer')
        
        # Предоставляем доступ вашему аккаунту (опционально)
        my_email = os.getenv('MY_ACC')  # Ваш email
        if my_email:
            new_sheet.share(my_email, perm_type='user', role='writer')
        
        return new_sheet.url
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")
        return None
    

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


def find_company_sheet_by_tgid(tgid):
    """
    Ищет таблицу компании по Telegram ID пользователя.
    Возвращает URL таблицы компании или None, если не найдено.
    """
    try:
        sheet = setup_google_sheets()
        all_values = sheet.get_all_values()
        
        # Ищем строку с нужным Telegram ID
        for row in all_values:
            if row[1] == str(tgid):  # Telegram ID во втором столбце
                return row[3]  # URL таблицы компании в четвертом столбце
        
        return None
    except Exception as e:
        print(f"Ошибка при поиске таблицы компании: {e}")
        return None
    
def get_managers_from_sheet(sheet_url: str) -> List[str]:
    """
    Получает список листов (менеджеров) из таблицы компании.
    Возвращает список названий листов или пустой список, если листов нет.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "/home/klim-petrov/projects/smartLITE/credentials.json", scope
        )
        client = gspread.authorize(creds)
        company_sheet = client.open_by_url(sheet_url)
        
        # Получаем список всех листов (менеджеров) в таблице
        worksheets = company_sheet.worksheets()
        managers = [ws.title for ws in worksheets if ws.title.startswith("Менеджер")]
        
        return managers
    except Exception as e:
        print(f"Ошибка при получении списка менеджеров: {e}")
        return []
    
def write_call_data_to_manager_sheet(
    sheet_url: str, manager_name: str, total_duration: float, is_qualified: bool, kval_percentage: float, parasite_words: str
):
    """
    Записывает данные о звонке в лист менеджера.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "/home/klim-petrov/projects/smartLITE/credentials.json", scope
        )
        client = gspread.authorize(creds)
        company_sheet = client.open_by_url(sheet_url)

        # Находим лист менеджера
        manager_sheet = company_sheet.worksheet(f"Менеджер {manager_name}")

        # Записываем данные в лист
        row_data = [
            total_duration,  # Время
            "Квал" if is_qualified else "Неквал",  # Квал/неквал
            kval_percentage,  # Процент квала
            parasite_words,  # Слова паразиты
        ]
        manager_sheet.append_row(row_data)

    except Exception as e:
        print(f"Ошибка при записи данных в лист менеджера: {e}")



def create_manager_sheet(sheet_url: str, manager_name: str):
    """
    Создает лист для менеджера с шапкой таблицы, если он еще не существует.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "/home/klim-petrov/projects/smartLITE/credentials.json", scope
        )
        client = gspread.authorize(creds)
        company_sheet = client.open_by_url(sheet_url)

        # Проверяем, существует ли лист менеджера
        try:
            manager_sheet = company_sheet.worksheet(f"Менеджер {manager_name}")
        except gspread.WorksheetNotFound:
            # Если лист не существует, создаем его
            manager_sheet = company_sheet.add_worksheet(title=f"Менеджер {manager_name}", rows="100", cols="20")
            # Создаем шапку таблицы
            header = ["Время звонка", "Квал/неквал", "%Квала", "СловаПаразиты"]
            manager_sheet.append_row(header)
        else:
            # Если лист существует, проверяем, есть ли шапка
            existing_data = manager_sheet.get_all_values()
            if not existing_data:  # Если лист пустой
                header = ["Время звонка", "Квал/неквал", "%Квала", "СловаПаразиты"]
                manager_sheet.append_row(header)

    except Exception as e:
        print(f"Ошибка при создании листа для менеджера: {e}")

def get_company_id_by_tgid(sheet, tgid: int) -> Optional[int]:
    """
    Ищет ID компании по Telegram ID пользователя.
    Возвращает ID компании или None, если не найдено.
    """
    try:
        all_values = sheet.get_all_values()
        for row in all_values:
            if row[1] == str(tgid):  # Telegram ID во втором столбце
                return int(row[0])  # ID компании в первом столбце
        return None
    except Exception as e:
        print(f"Ошибка при поиске ID компании: {e}")
        return None