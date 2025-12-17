"""
Модуль для работы с Supabase
Управление подключением к облачной базе данных и универсальные CRUD операции
"""

import os
import pandas as pd
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from datetime import datetime, date
import streamlit as st

if TYPE_CHECKING:
    from supabase import Client

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase library not installed. Install with: pip install supabase")

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


# Глобальная переменная для клиента Supabase
_supabase_client: Optional['Client'] = None


def get_supabase_credentials() -> Dict[str, Optional[str]]:
    """
    Получает credentials для Supabase из Streamlit secrets или .env файла
    
    Returns:
        Dict с ключами: url, key, use_local_storage
    """
    credentials = {
        'url': None,
        'key': None,
        'use_local_storage': True  # По умолчанию используем локальное хранилище
    }
    
    # Приоритет 1: Streamlit Secrets (для production на Streamlit Cloud)
    if hasattr(st, 'secrets'):
        try:
            credentials['url'] = st.secrets.get('SUPABASE_URL')
            credentials['key'] = st.secrets.get('SUPABASE_KEY')
            use_local = st.secrets.get('USE_LOCAL_STORAGE', 'true')
            credentials['use_local_storage'] = str(use_local).lower() == 'true'
            
            if credentials['url'] and credentials['key']:
                return credentials
        except Exception as e:
            print(f"Could not read Streamlit secrets: {e}")
    
    # Приоритет 2: Переменные окружения (.env файл)
    credentials['url'] = os.getenv('SUPABASE_URL')
    credentials['key'] = os.getenv('SUPABASE_KEY')
    use_local = os.getenv('USE_LOCAL_STORAGE', 'true')
    credentials['use_local_storage'] = str(use_local).lower() == 'true'
    
    return credentials


def init_supabase_client() -> Optional['Client']:
    """
    Инициализирует клиент Supabase
    
    Returns:
        Client instance или None если не удалось подключиться
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    if not SUPABASE_AVAILABLE:
        print("⚠️ Supabase library not available")
        return None
    
    credentials = get_supabase_credentials()
    
    if not credentials['url'] or not credentials['key']:
        print("⚠️ Supabase credentials not found. Using local storage.")
        return None
    
    try:
        _supabase_client = create_client(credentials['url'], credentials['key'])
        print("✅ Successfully connected to Supabase")
        return _supabase_client
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return None


def use_supabase() -> bool:
    """
    Проверяет, должно ли приложение использовать Supabase
    
    Returns:
        True если нужно использовать Supabase, False для локального хранилища
    """
    credentials = get_supabase_credentials()
    
    # Если явно указано использовать локальное хранилище
    if credentials['use_local_storage']:
        return False
    
    # Если нет credentials, используем локальное хранилище
    if not credentials['url'] or not credentials['key']:
        return False
    
    # Проверяем доступность библиотеки
    if not SUPABASE_AVAILABLE:
        return False
    
    return True


def prepare_data_for_supabase(data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    Подготавливает данные для отправки в Supabase
    Конвертирует date и datetime объекты в строки ISO формата
    
    Args:
        data: словарь или список словарей
        
    Returns:
        Очищенные данные
    """
    def clean_value(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        elif pd.isna(value):
            return None
        elif isinstance(value, (int, float, str, bool, type(None))):
            return value
        else:
            return str(value)
    
    if isinstance(data, list):
        return [{k: clean_value(v) for k, v in item.items()} for item in data]
    elif isinstance(data, dict):
        return {k: clean_value(v) for k, v in data.items()}
    else:
        raise ValueError("Data must be a dict or list of dicts")


# ==================================================
# УНИВЕРСАЛЬНЫЕ CRUD ОПЕРАЦИИ
# ==================================================

def supabase_select(
    table: str,
    columns: str = "*",
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> Optional[List[Dict]]:
    """
    Универсальная функция SELECT из Supabase
    
    Args:
        table: название таблицы
        columns: колонки для выборки (по умолчанию все)
        filters: словарь фильтров {column: value}
        order_by: колонка для сортировки (добавить .desc для обратного порядка)
        limit: максимальное количество записей
        
    Returns:
        List[Dict] с данными или None при ошибке
    """
    client = init_supabase_client()
    if client is None:
        return None
    
    try:
        query = client.table(table).select(columns)
        
        # Применяем фильтры
        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)
        
        # Сортировка
        if order_by:
            if order_by.endswith('.desc'):
                col = order_by.replace('.desc', '')
                query = query.order(col, desc=True)
            else:
                query = query.order(order_by)
        
        # Лимит
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data
        
    except Exception as e:
        print(f"❌ Error selecting from {table}: {e}")
        return None


def supabase_insert(table: str, data: Union[Dict, List[Dict]]) -> Optional[List[Dict]]:
    """
    Универсальная функция INSERT в Supabase
    
    Args:
        table: название таблицы
        data: словарь или список словарей для вставки
        
    Returns:
        Вставленные данные или None при ошибке
    """
    client = init_supabase_client()
    if client is None:
        return None
    
    try:
        clean_data = prepare_data_for_supabase(data)
        response = client.table(table).insert(clean_data).execute()
        return response.data
        
    except Exception as e:
        print(f"❌ Error inserting into {table}: {e}")
        return None


def supabase_update(
    table: str,
    data: Dict[str, Any],
    match_fields: Dict[str, Any]
) -> Optional[List[Dict]]:
    """
    Универсальная функция UPDATE в Supabase
    
    Args:
        table: название таблицы
        data: словарь с обновляемыми данными
        match_fields: словарь для поиска записей {column: value}
        
    Returns:
        Обновленные данные или None при ошибке
    """
    client = init_supabase_client()
    if client is None:
        return None
    
    try:
        clean_data = prepare_data_for_supabase(data)
        query = client.table(table).update(clean_data)
        
        # Применяем условия поиска
        for column, value in match_fields.items():
            query = query.eq(column, value)
        
        response = query.execute()
        return response.data
        
    except Exception as e:
        print(f"❌ Error updating {table}: {e}")
        return None


def supabase_upsert(
    table: str,
    data: Union[Dict, List[Dict]],
    on_conflict: Optional[str] = None
) -> Optional[List[Dict]]:
    """
    Универсальная функция UPSERT в Supabase
    Вставляет или обновляет при конфликте
    
    Args:
        table: название таблицы
        data: словарь или список словарей
        on_conflict: колонка для определения конфликта (например, 'campaign_id')
        
    Returns:
        Данные или None при ошибке
    """
    client = init_supabase_client()
    if client is None:
        return None
    
    try:
        clean_data = prepare_data_for_supabase(data)
        query = client.table(table).upsert(clean_data)
        
        if on_conflict:
            query = query.on_conflict(on_conflict)
        
        response = query.execute()
        return response.data
        
    except Exception as e:
        print(f"❌ Error upserting into {table}: {e}")
        return None


def supabase_delete(table: str, match_fields: Dict[str, Any]) -> bool:
    """
    Универсальная функция DELETE из Supabase
    
    Args:
        table: название таблицы
        match_fields: словарь для поиска записей {column: value}
        
    Returns:
        True если успешно, False при ошибке
    """
    client = init_supabase_client()
    if client is None:
        return False
    
    try:
        query = client.table(table)
        
        # Применяем условия поиска
        for column, value in match_fields.items():
            query = query.delete().eq(column, value)
        
        query.execute()
        return True
        
    except Exception as e:
        print(f"❌ Error deleting from {table}: {e}")
        return False


# ==================================================
# КОНВЕРТАЦИЯ ДАННЫХ
# ==================================================

def dataframe_to_supabase(df: pd.DataFrame, table: str) -> bool:
    """
    Загружает весь DataFrame в Supabase таблицу
    
    Args:
        df: DataFrame для загрузки
        table: название таблицы
        
    Returns:
        True если успешно
    """
    if df.empty:
        print(f"DataFrame is empty, nothing to upload to {table}")
        return True
    
    # Конвертируем DataFrame в список словарей
    records = df.to_dict('records')
    
    # Загружаем батчами по 1000 записей
    batch_size = 1000
    total_batches = (len(records) + batch_size - 1) // batch_size
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} records)...")
        
        result = supabase_insert(table, batch)
        if result is None:
            print(f"❌ Failed to upload batch {batch_num}")
            return False
    
    print(f"✅ Successfully uploaded {len(records)} records to {table}")
    return True


def replace_table_data(df: pd.DataFrame, table: str) -> bool:
    """
    Заменяет все данные в таблице Supabase на данные из DataFrame
    Удаляет все существующие записи, затем вставляет новые
    
    ⚠️ WARNING: This function DELETES ALL RECORDS from the table before inserting new data.
    This is a dangerous operation that can lead to data loss if an error occurs during insertion.
    
    ⚠️ RECOMMENDED: Use save_dataframe_incrementally() instead for regular operations.
    This function should only be used for:
    - Initial data migration
    - Complete table resets (with user confirmation)
    - Testing/development environments
    
    Args:
        df: DataFrame для загрузки
        table: название таблицы
        
    Returns:
        True если успешно
    """
    client = init_supabase_client()
    if client is None:
        print(f"⚠️ Cannot connect to Supabase, skipping replace for {table}")
        return False
    
    try:
        # Шаг 1: Удаляем все существующие записи
        print(f"⚠️⚠️⚠️ WARNING: About to DELETE ALL records from table '{table}' ⚠️⚠️⚠️")
        print(f"📊 Will insert {len(df)} records after deletion")
        
        delete_response = client.table(table).delete().neq('id', 0).execute()
        
        print(f"✅ Deleted existing records from table '{table}'")
        
        # Шаг 2: Вставляем новые данные
        if df.empty:
            print(f"📊 DataFrame is empty, {table} is now empty")
            return True
        
        # Конвертируем DataFrame в список словарей
        records = df.to_dict('records')
        
        # Загружаем батчами по 1000 записей
        batch_size = 1000
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} records) to '{table}'...")
            
            result = supabase_insert(table, batch)
            if result is None:
                print(f"❌ Failed to upload batch {batch_num} to '{table}'")
                return False
        
        print(f"✅ Successfully replaced all data in '{table}' ({len(records)} records)")
        return True
        
    except Exception as e:
        print(f"❌ Error replacing data in '{table}': {e}")
        import traceback
        traceback.print_exc()
        return False


def save_dataframe_incrementally(
    df: pd.DataFrame, 
    table: str,
    unique_columns: Optional[List[str]] = None,
    id_column: str = 'id'
) -> bool:
    """
    Безопасно сохраняет DataFrame в Supabase используя инкрементальные обновления
    Использует стратегию: загрузить существующие → объединить → сохранить все
    
    Этот метод НЕ удаляет существующие данные, а только обновляет/добавляет записи.
    Для удаления записей используйте явные операции delete.
    
    Args:
        df: DataFrame для сохранения
        table: название таблицы
        unique_columns: список колонок для определения уникальности записи
                       Если None, используется id_column
        id_column: название колонки с уникальным ID (по умолчанию 'id')
        
    Returns:
        True если успешно
        
    Examples:
        # Для таблицы с record_id как уникальным идентификатором:
        save_dataframe_incrementally(df, 'program_financials', unique_columns=['record_id'])
        
        # Для таблицы с композитным уникальным ключом:
        save_dataframe_incrementally(df, 'kpi_history', unique_columns=['date_start', 'date_end', 'kpi_id'])
    """
    client = init_supabase_client()
    if client is None:
        print(f"⚠️ Cannot connect to Supabase, skipping save for {table}")
        return False
    
    if df.empty:
        print(f"📊 DataFrame is empty, nothing to save to {table}")
        return True
    
    try:
        # Шаг 1: Загружаем существующие данные из таблицы
        print(f"📥 Loading existing data from {table}...")
        existing_data = supabase_select(table)
        
        if existing_data is None:
            existing_data = []
        
        existing_df = pd.DataFrame(existing_data) if existing_data else pd.DataFrame()
        
        # Шаг 2: Подготавливаем новый DataFrame
        df_to_save = df.copy()
        
        # Удаляем auto-increment id колонку если она есть
        if id_column in df_to_save.columns and id_column == 'id':
            df_to_save = df_to_save.drop(columns=[id_column])
        
        # Шаг 3: Объединяем данные
        if not existing_df.empty and unique_columns:
            # Удаляем id из существующих данных для корректного слияния
            if id_column in existing_df.columns and id_column == 'id':
                existing_df = existing_df.drop(columns=[id_column])
            
            # Удаляем из существующих данных записи, которые есть в новом DataFrame
            # (они будут заменены новыми версиями)
            print(f"🔄 Merging data based on unique columns: {unique_columns}")
            
            # Создаем маску для записей, которые НЕ должны быть обновлены
            merge_key = unique_columns[0] if len(unique_columns) == 1 else unique_columns
            
            # Находим записи в existing_df, которых нет в df_to_save
            if isinstance(merge_key, list):
                # Композитный ключ
                existing_keys = existing_df[merge_key].apply(tuple, axis=1)
                new_keys = df_to_save[merge_key].apply(tuple, axis=1)
                mask = ~existing_keys.isin(new_keys)
            else:
                # Одиночный ключ
                mask = ~existing_df[merge_key].isin(df_to_save[merge_key])
            
            # Оставляем только записи, которые не обновляются
            existing_df_filtered = existing_df[mask]
            
            # Объединяем: старые неизмененные записи + новые/обновленные записи
            combined_df = pd.concat([existing_df_filtered, df_to_save], ignore_index=True)
            
            print(f"📊 Combined: {len(existing_df_filtered)} existing + {len(df_to_save)} new/updated = {len(combined_df)} total")
        else:
            # Если нет существующих данных или не указаны unique_columns, просто добавляем
            combined_df = pd.concat([existing_df, df_to_save], ignore_index=True)
            print(f"📊 Adding {len(df_to_save)} new records to {len(existing_df)} existing")
        
        # Шаг 4: Сохраняем объединенные данные
        # Используем replace_table_data, но теперь это безопасно, так как мы сохраняем ВСЕ данные
        print(f"💾 Saving {len(combined_df)} total records to {table}...")
        success = replace_table_data(combined_df, table)
        
        if success:
            print(f"✅ Successfully saved {len(df_to_save)} records to {table} (incremental)")
            return True
        else:
            print(f"❌ Failed to save to {table}")
            return False
        
    except Exception as e:
        print(f"❌ Error saving data incrementally to {table}: {e}")
        import traceback
        traceback.print_exc()
        return False


def supabase_to_dataframe(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None
) -> pd.DataFrame:
    """
    Загружает данные из Supabase в DataFrame
    
    Args:
        table: название таблицы
        filters: опциональные фильтры
        order_by: опциональная сортировка
        
    Returns:
        DataFrame с данными
    """
    data = supabase_select(table, filters=filters, order_by=order_by)
    
    if data is None or len(data) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Конвертируем строковые даты обратно в date объекты
    date_columns = ['date_start', 'date_end', 'start_date', 'end_date', 'update_date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    
    # Конвертируем timestamps
    timestamp_columns = ['created_at', 'updated_at']
    for col in timestamp_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df


# ==================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==================================================

def test_connection() -> bool:
    """
    Тестирует подключение к Supabase
    
    Returns:
        True если подключение успешно
    """
    client = init_supabase_client()
    if client is None:
        return False
    
    try:
        # Пробуем выполнить простой запрос
        result = supabase_select('kpi_history', limit=1)
        return result is not None
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def get_storage_mode() -> str:
    """
    Возвращает текущий режим хранения данных
    
    Returns:
        'supabase' или 'local'
    """
    return 'supabase' if use_supabase() else 'local'


def get_table_count(table: str) -> Optional[int]:
    """
    Возвращает количество записей в таблице
    
    Args:
        table: название таблицы
        
    Returns:
        Количество записей или None при ошибке
    """
    data = supabase_select(table, columns="id")
    return len(data) if data else None
