"""
Модуль управления данными кампаний
Отвечает за хранение, загрузку и базовые операции CRUD
Использует JSON для хранения и поддерживает автоматические бэкапы.
"""

import pandas as pd
import json
import os
import shutil
import glob
from datetime import datetime, date
from typing import Dict, List, Optional, Any

# Пути к файлам
DATA_DIR = "data"
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

# Основные файлы (JSON)
CAMPAIGNS_FILE_JSON = os.path.join(DATA_DIR, "campaigns.json")
COLLECTION_HISTORY_FILE_JSON = os.path.join(DATA_DIR, "collection_history.json")

# Устаревшие файлы (Pickle) - для миграции
CAMPAIGNS_FILE_PKL = os.path.join(DATA_DIR, "campaigns.pkl")
COLLECTION_HISTORY_FILE_PKL = os.path.join(DATA_DIR, "collection_history.pkl")


def ensure_directories():
    """Создает необходимые директории"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def create_backup(file_path: str):
    """
    Создает бэкап файла с timestamp.
    Оставляет только последние 10 бэкапов.
    """
    if not os.path.exists(file_path):
        return

    ensure_directories()
    
    filename = os.path.basename(file_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"{filename}.{timestamp}.bak")
    
    try:
        shutil.copy2(file_path, backup_path)
        
        # Очистка старых бэкапов (оставляем 10 последних для этого типа файла)
        pattern = os.path.join(BACKUP_DIR, f"{filename}.*.bak")
        backups = sorted(glob.glob(pattern))
        
        while len(backups) > 10:
            os.remove(backups.pop(0))
            
    except Exception as e:
        print(f"Ошибка создания бэкапа для {filename}: {e}")


def migrate_pickle_to_json(pkl_path: str, json_path: str):
    """
    Мигрирует данные из pickle в json, если json не существует.
    """
    if not os.path.exists(pkl_path):
        return
        
    if os.path.exists(json_path):
        return

    print(f"Миграция данных из {pkl_path} в {json_path}...")
    try:
        import pickle
        with open(pkl_path, 'rb') as f:
            df = pickle.load(f)
            
        if isinstance(df, pd.DataFrame) and not df.empty:
            # Конвертация дат в строки для JSON
            # Pandas to_json с date_format='iso' сделает это, но для надежности
            # при чтении мы будем парсить даты обратно
            df.to_json(json_path, orient='records', date_format='iso', indent=2, force_ascii=False)
            print("Миграция успешна.")
            
            # Бэкапим старый pkl
            create_backup(pkl_path)
    except Exception as e:
        print(f"Ошибка миграции: {e}")


def create_empty_campaigns_df() -> pd.DataFrame:
    """Создает пустой DataFrame для кампаний с правильной структурой"""
    return pd.DataFrame(columns=[
        'campaign_id',           # Уникальный ID
        'group_id',              # ID группы (для мультиканальности)
        'name',                  # Название кампании
        'channel',               # Канал (VK, Telegram, Email, Website)
        'start_date',            # Дата старта
        'end_date',              # Дата окончания
        'status',                # active/completed/paused
        'target_amount',         # Цель сбора (руб.)
        'collected_amount',      # Собрано (руб.)
        'ad_costs',              # Затраты на рекламу (руб.)
        'labor_hours',           # Трудозатраты (часы)
        'hourly_rate',           # Стоимость часа (руб.)
        'reach',                 # Охват (просмотры)
        'clicks',                # Клики
        'conversions',           # Конверсии (целевые действия)
        'donors_count',          # Количество доноров
        'description',           # Описание кампании
        'created_at',            # Дата создания записи
        'updated_at'             # Дата последнего обновления
    ])


def load_campaigns() -> pd.DataFrame:
    """Загружает кампании из JSON файла"""
    ensure_directories()
    
    # Попытка миграции, если есть старый файл и нет нового
    migrate_pickle_to_json(CAMPAIGNS_FILE_PKL, CAMPAIGNS_FILE_JSON)
    
    if os.path.exists(CAMPAIGNS_FILE_JSON):
        try:
            df = pd.read_json(CAMPAIGNS_FILE_JSON, orient='records')
            
            # Восстановление типов дат
            date_cols = ['start_date', 'end_date', 'created_at', 'updated_at']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col]).dt.date
                    # created_at и updated_at могут быть datetime, но для совместимости пока date
                    # Если нужны datetime, можно убрать .dt.date для них
            
            # created_at/updated_at лучше оставить datetime
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at'])

            if not df.empty:
                return df
                
        except ValueError as e:
            # Ошибка декодирования JSON или пустой файл
            print(f"Ошибка чтения JSON кампаний: {e}")
            # Бэкапим поврежденный файл
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            corrupted_path = f"{CAMPAIGNS_FILE_JSON}.corrupted.{timestamp}"
            shutil.copy2(CAMPAIGNS_FILE_JSON, corrupted_path)
            print(f"Поврежденный файл сохранен как {corrupted_path}")
    
    return create_empty_campaigns_df()


def save_campaigns(df: pd.DataFrame) -> bool:
    """Сохраняет кампании в JSON файл с бэкапом"""
    ensure_directories()
    
    try:
        # Создаем бэкап перед записью
        create_backup(CAMPAIGNS_FILE_JSON)
        
        # Сохраняем
        df.to_json(CAMPAIGNS_FILE_JSON, orient='records', date_format='iso', indent=2, force_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка сохранения кампаний: {e}")
        return False


def generate_campaign_id() -> str:
    """Генерирует уникальный ID кампании"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"CAMP_{timestamp}"


def add_campaign(
    name: str,
    channel: str,
    start_date: date,
    end_date: date,
    target_amount: float,
    group_id: str = None,
    collected_amount: float = 0.0,
    ad_costs: float = 0.0,
    labor_hours: float = 0.0,
    hourly_rate: float = 500.0,
    reach: int = 0,
    clicks: int = 0,
    conversions: int = 0,
    donors_count: int = 0,
    description: str = "",
    status: str = "active"
) -> Dict[str, Any]:
    """
    Добавляет новую кампанию
    """
    try:
        df = load_campaigns()
        
        campaign_id = generate_campaign_id()
        now = datetime.now()
        
        new_campaign = {
            'campaign_id': campaign_id,
            'group_id': group_id,
            'name': name,
            'channel': channel,
            'start_date': start_date,
            'end_date': end_date,
            'status': status,
            'target_amount': target_amount,
            'collected_amount': collected_amount,
            'ad_costs': ad_costs,
            'labor_hours': labor_hours,
            'hourly_rate': hourly_rate,
            'reach': reach,
            'clicks': clicks,
            'conversions': conversions,
            'donors_count': donors_count,
            'description': description,
            'created_at': now,
            'updated_at': now
        }
        
        new_df = pd.DataFrame([new_campaign])
        df = pd.concat([df, new_df], ignore_index=True)
        
        if save_campaigns(df):
            return {
                'success': True,
                'campaign_id': campaign_id,
                'message': f"Кампания '{name}' успешно создана"
            }
        else:
            return {
                'success': False,
                'campaign_id': None,
                'message': "Ошибка сохранения кампании"
            }
            
    except Exception as e:
        return {
            'success': False,
            'campaign_id': None,
            'message': f"Ошибка создания кампании: {str(e)}"
        }


def update_campaign(campaign_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Обновляет данные кампании
    """
    try:
        df = load_campaigns()
        
        if campaign_id not in df['campaign_id'].values:
            return {
                'success': False,
                'message': f"Кампания {campaign_id} не найдена"
            }
        
        # Обновляем поля
        mask = df['campaign_id'] == campaign_id
        for field, value in updates.items():
            if field in df.columns and field != 'campaign_id':
                df.loc[mask, field] = value
        
        # Обновляем timestamp
        df.loc[mask, 'updated_at'] = datetime.now()
        
        if save_campaigns(df):
            return {
                'success': True,
                'message': f"Кампания {campaign_id} обновлена"
            }
        else:
            return {
                'success': False,
                'message': "Ошибка сохранения изменений"
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f"Ошибка обновления: {str(e)}"
        }


def delete_campaign(campaign_id: str) -> Dict[str, Any]:
    """Удаляет кампанию по ID"""
    try:
        df = load_campaigns()
        
        if campaign_id not in df['campaign_id'].values:
            return {
                'success': False,
                'message': f"Кампания {campaign_id} не найдена"
            }
        
        df = df[df['campaign_id'] != campaign_id]
        
        if save_campaigns(df):
            return {
                'success': True,
                'message': f"Кампания {campaign_id} удалена"
            }
        else:
            return {
                'success': False,
                'message': "Ошибка сохранения изменений"
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f"Ошибка удаления: {str(e)}"
        }


def get_campaign_by_id(campaign_id: str) -> Optional[pd.Series]:
    """Возвращает кампанию по ID"""
    df = load_campaigns()
    
    if campaign_id in df['campaign_id'].values:
        return df[df['campaign_id'] == campaign_id].iloc[0]
    
    return None


def get_active_campaigns() -> pd.DataFrame:
    """Возвращает только активные кампании"""
    df = load_campaigns()
    return df[df['status'] == 'active']


def get_campaigns_by_channel(channel: str) -> pd.DataFrame:
    """Возвращает кампании по каналу"""
    df = load_campaigns()
    return df[df['channel'] == channel]


def get_campaigns_by_date_range(start_date: date, end_date: date) -> pd.DataFrame:
    """Возвращает кампании в заданном диапазоне дат"""
    df = load_campaigns()
    
    # Конвертируем даты для сравнения
    df['start_date_dt'] = pd.to_datetime(df['start_date'])
    df['end_date_dt'] = pd.to_datetime(df['end_date'])
    
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)
    
    # Кампании, которые пересекаются с указанным диапазоном
    mask = (df['start_date_dt'] <= end_dt) & (df['end_date_dt'] >= start_dt)
    
    return df[mask].drop(columns=['start_date_dt', 'end_date_dt'])


def get_campaign_groups() -> List[str]:
    """Возвращает список уникальных групп кампаний"""
    df = load_campaigns()
    if 'group_id' not in df.columns:
        return []
    groups = df['group_id'].dropna().unique().tolist()
    return groups


# --- ИСТОРИЯ СБОРОВ ---

def create_empty_collection_history_df() -> pd.DataFrame:
    """Создает пустой DataFrame для истории сборов"""
    return pd.DataFrame(columns=[
        'history_id',           # Уникальный ID записи
        'campaign_id',          # ID кампании
        'update_date',          # Дата обновления
        'amount_added',         # Добавленная сумма
        'total_after_update',   # Общая сумма после обновления
        'note',                 # Примечание/комментарий
        'created_at'            # Время создания записи
    ])


def load_collection_history() -> pd.DataFrame:
    """Загружает историю сборов из JSON файла"""
    ensure_directories()
    
    # Миграция
    migrate_pickle_to_json(COLLECTION_HISTORY_FILE_PKL, COLLECTION_HISTORY_FILE_JSON)
    
    if os.path.exists(COLLECTION_HISTORY_FILE_JSON):
        try:
            df = pd.read_json(COLLECTION_HISTORY_FILE_JSON, orient='records')
            
            # Восстановление дат
            if 'update_date' in df.columns:
                df['update_date'] = pd.to_datetime(df['update_date']).dt.date
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
                
            if not df.empty:
                return df
        except ValueError as e:
            print(f"Ошибка чтения JSON истории: {e}")
            # Бэкапим
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            corrupted_path = f"{COLLECTION_HISTORY_FILE_JSON}.corrupted.{timestamp}"
            shutil.copy2(COLLECTION_HISTORY_FILE_JSON, corrupted_path)
    
    return create_empty_collection_history_df()


def save_collection_history(df: pd.DataFrame) -> bool:
    """Сохраняет историю сборов в JSON файл с бэкапом"""
    ensure_directories()
    
    try:
        create_backup(COLLECTION_HISTORY_FILE_JSON)
        df.to_json(COLLECTION_HISTORY_FILE_JSON, orient='records', date_format='iso', indent=2, force_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка сохранения истории сборов: {e}")
        return False


def add_collection_update(
    campaign_id: str,
    amount_added: float,
    note: str = "",
    update_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Добавляет новую запись в историю сборов и обновляет общую сумму кампании
    """
    try:
        # Загружаем данные
        campaigns_df = load_campaigns()
        history_df = load_collection_history()
        
        # Проверяем существование кампании
        if campaign_id not in campaigns_df['campaign_id'].values:
            return {
                'success': False,
                'message': f"Кампания {campaign_id} не найдена"
            }
        
        # Получаем текущую сумму
        campaign = campaigns_df[campaigns_df['campaign_id'] == campaign_id].iloc[0]
        current_amount = float(campaign['collected_amount'])
        new_total = current_amount + amount_added
        
        # Создаем запись в истории
        if update_date is None:
            update_date = datetime.now().date()
        
        history_id = f"HIST_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        new_history_record = {
            'history_id': history_id,
            'campaign_id': campaign_id,
            'update_date': update_date,
            'amount_added': amount_added,
            'total_after_update': new_total,
            'note': note,
            'created_at': datetime.now()
        }
        
        # Добавляем в историю
        new_history_df = pd.DataFrame([new_history_record])
        history_df = pd.concat([history_df, new_history_df], ignore_index=True)
        
        # Обновляем кампанию
        campaigns_df.loc[campaigns_df['campaign_id'] == campaign_id, 'collected_amount'] = new_total
        campaigns_df.loc[campaigns_df['campaign_id'] == campaign_id, 'updated_at'] = datetime.now()
        
        # Сохраняем
        if save_collection_history(history_df) and save_campaigns(campaigns_df):
            return {
                'success': True,
                'message': f"Добавлено {amount_added:,.0f} ₽. Новая общая сумма: {new_total:,.0f} ₽",
                'new_total': new_total,
                'amount_added': amount_added
            }
        else:
            return {
                'success': False,
                'message': "Ошибка сохранения данных"
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f"Ошибка добавления сбора: {str(e)}"
        }


def get_collection_history(campaign_id: str) -> pd.DataFrame:
    """Возвращает историю сборов для конкретной кампании"""
    history_df = load_collection_history()
    
    if history_df.empty:
        return history_df
    
    return history_df[history_df['campaign_id'] == campaign_id].sort_values(
        'update_date', ascending=False
    )


def get_collection_summary(campaign_id: str) -> Dict[str, Any]:
    """Возвращает сводку по сборам кампании"""
    history_df = get_collection_history(campaign_id)
    campaign = get_campaign_by_id(campaign_id)
    
    if campaign is None:
        return {}
    
    if history_df.empty:
        return {
            'total_collected': campaign['collected_amount'],
            'updates_count': 0,
            'last_update_date': None,
            'last_update_amount': 0,
            'average_update': 0
        }
    
    return {
        'total_collected': campaign['collected_amount'],
        'updates_count': len(history_df),
        'last_update_date': history_df.iloc[0]['update_date'],
        'last_update_amount': history_df.iloc[0]['amount_added'],
        'average_update': history_df['amount_added'].mean()
    }
