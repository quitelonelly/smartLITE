import os
from typing import List
from oauth2client.service_account import ServiceAccountCredentials
import gspread

def is_user_registered(sheet, tgid: int) -> bool:
    """
    Проверяет, зарегистрирован ли пользователь по его telegram_id.
    Возвращает True, если зарегистрирован, иначе False.
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