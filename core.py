import os
from typing import List, Optional
from oauth2client.service_account import ServiceAccountCredentials
import gspread

def is_user_registered(sheet, tgid: int) -> bool:
    """
    Проверяет, зарегистрирован ли пользователь по его telegram_id.
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
    sheet_url: str,
    manager_name: str,
    transcription_data: dict,
    total_duration: float,
    call_datetime: str = None
):
    """
    Записывает данные звонка и суммирует токены в указанный столбец
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "/home/klim-petrov/projects/smartLITE/credentials.json", scope
        )
        client = gspread.authorize(creds)
        
        # 1. Открываем главную таблицу
        main_sheet = client.open_by_key("1CoDQJn0T_scUV7ZsbYU8x2nZTzu_F9CBrculeQIG2KA").sheet1
        
        # 2. Находим столбец "token" (колонка E)
        token_column = 11 # Колонка E (5-я колонка)
        
        # 3. Получаем все значения из столбца
        tokens_column_values = main_sheet.col_values(token_column)
        
        # 4. Суммируем существующие значения (пропускаем заголовок)
        total_tokens = 0
        for i, value in enumerate(tokens_column_values[1:], start=2):  # Пропускаем заголовок
            try:
                total_tokens += int(value) if value else 0
            except ValueError:
                print(f"Ошибка преобразования значения в строке {i}: {value}")
        
        # 5. Добавляем новые токены
        new_tokens = transcription_data.get("token_usage", {}).get("total", 0)
        total_tokens += new_tokens
        
        # 6. Обновляем последнюю ячейку в столбце
        last_row = len(tokens_column_values) + 1
        main_sheet.update_cell(last_row, token_column, str(total_tokens))
        
        # 7. Записываем данные в таблицу менеджера (как раньше)
        company_sheet = client.open_by_url(sheet_url)
        manager_sheet = company_sheet.worksheet(f"Менеджер {manager_name}")

        if call_datetime is None:
            from datetime import datetime
            call_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row_data = [
            call_datetime,
            total_duration,
            transcription_data.get("manager_evaluation", {}).get("score", 0),
            "\n".join(transcription_data.get("manager_errors", [])),
            transcription_data.get("dialogue_outcomes", ""),
            "Да" if transcription_data.get("lead_qualification", {}).get("qualified", "нет") == "да" else "Нет",
            "\n".join(transcription_data.get("lead_qualification", {}).get("criteria", [])),
            transcription_data.get("objection_handling", {}).get("evaluation", "N/A"),
            transcription_data.get("client_readiness", {}).get("level", "Не определено"),
            transcription_data.get("client_readiness", {}).get("explanation", ""),
            transcription_data.get("manager_confidence", {}).get("confidence", "Не уверен"),
            transcription_data.get("product_expertise", {}).get("level", "N/A"),
            "\n---\n".join(
                f"Цитата: {rec['error']['quote']}\nАнализ: {rec['error']['analysis']}\nСовет: {rec['error']['advice']}"
                for rec in transcription_data.get("recommendations", [])
            ) if transcription_data.get("recommendations") else "Нет рекомендаций",
            str(new_tokens)  # Добавляем использованные токены в конец строки
        ]

        manager_sheet.append_row(row_data)
        
        print(f"Успешно записано. Новые токены: {new_tokens}, Общий баланс: {total_tokens}")

    except Exception as e:
        print(f"Ошибка при записи данных: {str(e)}")
        raise


def create_manager_sheet(sheet_url: str, manager_name: str):
    """
    Создает лист для менеджера с полной шапкой таблицы анализа звонков
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "/home/klim-petrov/projects/smartLITE/credentials.json", scope
        )
        client = gspread.authorize(creds)
        company_sheet = client.open_by_url(sheet_url)

        sheet_title = f"Менеджер {manager_name}"
        
        try:
            manager_sheet = company_sheet.worksheet(sheet_title)
        except gspread.WorksheetNotFound:
            manager_sheet = company_sheet.add_worksheet(title=sheet_title, rows="1000", cols="20")
        
        # Полная шапка таблицы
        header = [
            "Дата и время",
            "Общее время звонка (сек)",
            "Оценка менеджера (%)",
            "Ошибки менеджера",
            "Итог диалога",
            "Квалификация лида",
            "Критерии квалификации",
            "Отработка возражений",
            "Готовность клиента",
            "Пояснение готовности",
            "Уверенность менеджера",
            "Экспертиза в продукте",
            "Рекомендации",
        ]
        
        manager_sheet.append_row(header)
        
        # Настраиваем форматирование
        header_format = {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8}
        }
        manager_sheet.format("A1:M1", header_format)

    except Exception as e:
        print(f"error: {e}")
        raise

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
    
def check_and_mark_key(sheet, key):
    """
    Проверяет ключ в листе 'Keys' и отмечает его как использованный, если он не использован.
    Возвращает True, если ключ валиден и был успешно отмечен, False в противном случае.
    """
    try:
        # Получаем доступ ко всей таблице, а не к конкретному листу
        spreadsheet = sheet.spreadsheet
        
        # Получаем лист 'Keys'
        try:
            keys_sheet = spreadsheet.worksheet('Keys')
        except gspread.WorksheetNotFound:
            print("Лист 'Keys' не найден в таблице")
            return False
        
        # Получаем все ключи и их статусы
        keys = keys_sheet.col_values(1)  # Первый столбец - ключи
        statuses = keys_sheet.col_values(2)  # Второй столбец - статусы
        
        # Ищем ключ в списке
        for i, (k, s) in enumerate(zip(keys, statuses), start=1):
            if k == key:
                if s.lower() == 'false' or s == '':
                    # Помечаем ключ как использованный
                    keys_sheet.update_cell(i, 2, 'TRUE')
                    return True
                else:
                    return False
        return False
    except Exception as e:
        print(f"Ошибка при проверке ключа: {e}")
        return False