"""
Скрипт для миграции данных из локальных файлов в Supabase
Запустите этот скрипт один раз для переноса существующих данных
"""

import os
import sys
import pandas as pd
import pickle
import json
from datetime import datetime

# Добавляем текущую директорию в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Импортируем модули
try:
    from modules.supabase_manager import (
        dataframe_to_supabase,
        use_supabase,
        test_connection,
        get_table_count
    )
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Ошибка импорта Supabase manager: {e}")
    print("Убедитесь, что установлены зависимости: pip install supabase python-dotenv")
    sys.exit(1)

# Пути к файлам
BACKUP_FILE = "kpi_backup.pkl"
CAMPAIGNS_FILE = "data/campaigns.json"
CAMPAIGNS_PKL = "data/campaigns.pkl"
COLLECTION_HISTORY_FILE = "data/collection_history.json"
COLLECTION_HISTORY_PKL = "data/collection_history.pkl"
PROGRAM_FINANCIALS_FILE = "data/program_financials.pkl"


def backup_local_files():
    """Создает резервные копии всех локальных файлов перед миграцией"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backup_before_migration_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"\n📦 Создание backup в директории: {backup_dir}")
    
    files_to_backup = [
        BACKUP_FILE,
        CAMPAIGNS_FILE,
        CAMPAIGNS_PKL,
        COLLECTION_HISTORY_FILE,
        COLLECTION_HISTORY_PKL,
        PROGRAM_FINANCIALS_FILE
    ]
    
    backed_up = 0
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            import shutil
            dest = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest)
            print(f"  ✅ {file_path} -> {dest}")
            backed_up += 1
    
    print(f"\n📊 Создано {backed_up} backup файлов")
    return backup_dir


def migrate_kpi_history():
    """Миграция KPI history из pickle файла"""
    print("\n🔄 Миграция KPI History...")
    
    if not os.path.exists(BACKUP_FILE):
        print("  ⚠️ Файл kpi_backup.pkl не найден")
        return False
    
    try:
        with open(BACKUP_FILE, 'rb') as f:
            df = pickle.load(f)
        
        if df.empty:
            print("  📊 KPI history пуст, пропускаем")
            return True
        
        print(f"  📊 Найдено {len(df)} записей KPI")
        
        # Преобразуем колонки для Supabase
        column_mapping = {
            'Дата_Начала': 'date_start',
            'Дата_Окончания': 'date_end',
            'Неделя_Год': 'week_year',
            'Промежуток_Дат': 'date_range',
            'Категория': 'category',
            'KPI_ID': 'kpi_id',
            'Название': 'name',
            'Минимум': 'minimum',
            'Цель': 'target',
            'Факт': 'actual',
            'Комментарий': 'comment'
        }
        
        df_clean = df.copy()
        df_clean = df_clean.rename(columns=column_mapping)
        
        # Добавляем timestamps
        df_clean['created_at'] = datetime.now()
        df_clean['updated_at'] = datetime.now()
        
        # Загружаем в Supabase
        success = dataframe_to_supabase(df_clean, 'kpi_history')
        
        if success:
            print(f"  ✅ Успешно загружено {len(df)} записей в kpi_history")
            return True
        else:
            print("  ❌ Ошибка загрузки в Supabase")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка миграции KPI history: {e}")
        return False


def migrate_campaigns():
    """Миграция кампаний из JSON файла"""
    print("\n🔄 Миграция Campaigns...")
    
    # Пробуем сначала JSON, потом PKL
    df = None
    
    if os.path.exists(CAMPAIGNS_FILE):
        try:
            df = pd.read_json(CAMPAIGNS_FILE, orient='records')
            print(f"  📊 Загружено из {CAMPAIGNS_FILE}")
        except:
            pass
    
    if df is None and os.path.exists(CAMPAIGNS_PKL):
        try:
            with open(CAMPAIGNS_PKL, 'rb') as f:
                df = pickle.load(f)
            print(f"  📊 Загружено из {CAMPAIGNS_PKL}")
        except:
            pass
    
    if df is None:
        print("  ⚠️ Файлы campaigns не найдены")
        return False
    
    if df.empty:
        print("  📊 Campaigns пуст, пропускаем")
        return True
    
    print(f"  📊 Найдено {len(df)} кампаний")
    
    try:
        df_clean = df.copy()
        
        # Удаляем id если есть
        if 'id' in df_clean.columns:
            df_clean = df_clean.drop(columns=['id'])
        
        # Загружаем в Supabase
        success = dataframe_to_supabase(df_clean, 'campaigns')
        
        if success:
            print(f"  ✅ Успешно загружено {len(df)} кампаний")
            return True
        else:
            print("  ❌ Ошибка загрузки в Supabase")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка миграции campaigns: {e}")
        return False


def migrate_collection_history():
    """Миграция истории сборов"""
    print("\n🔄 Миграция Collection History...")
    
    df = None
    
    if os.path.exists(COLLECTION_HISTORY_FILE):
        try:
            df = pd.read_json(COLLECTION_HISTORY_FILE, orient='records')
            print(f"  📊 Загружено из {COLLECTION_HISTORY_FILE}")
        except:
            pass
    
    if df is None and os.path.exists(COLLECTION_HISTORY_PKL):
        try:
            with open(COLLECTION_HISTORY_PKL, 'rb') as f:
                df = pickle.load(f)
            print(f"  📊 Загружено из {COLLECTION_HISTORY_PKL}")
        except:
            pass
    
    if df is None:
        print("  ⚠️ Файлы collection_history не найдены")
        return False
    
    if df.empty:
        print("  📊 Collection history пуст, пропускаем")
        return True
    
    print(f"  📊 Найдено {len(df)} записей истории")
    
    try:
        df_clean = df.copy()
        
        if 'id' in df_clean.columns:
            df_clean = df_clean.drop(columns=['id'])
        
        success = dataframe_to_supabase(df_clean, 'collection_history')
        
        if success:
            print(f"  ✅ Успешно загружено {len(df)} записей")
            return True
        else:
            print("  ❌ Ошибка загрузки в Supabase")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка миграции collection_history: {e}")
        return False


def migrate_program_financials():
    """Миграция финансовых данных программ"""
    print("\n🔄 Миграция Program Financials...")
    
    if not os.path.exists(PROGRAM_FINANCIALS_FILE):
        print("  ⚠️ Файл program_financials.pkl не найден")
        return False
    
    try:
        with open(PROGRAM_FINANCIALS_FILE, 'rb') as f:
            df = pickle.load(f)
        
        if df.empty:
            print("  📊 Program financials пуст, пропускаем")
            return True
        
        print(f"  📊 Найдено {len(df)} записей")
        
        df_clean = df.copy()
        
        if 'id' in df_clean.columns:
            df_clean = df_clean.drop(columns=['id'])
        
        success = dataframe_to_supabase(df_clean, 'program_financials')
        
        if success:
            print(f"  ✅ Успешно загружено {len(df)} записей")
            return True
        else:
            print("  ❌ Ошибка загрузки в Supabase")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка миграции program_financials: {e}")
        return False


def verify_migration():
    """Проверка успешности миграции"""
    print("\n🔍 Проверка миграции...")
    
    tables = ['kpi_history', 'campaigns', 'collection_history', 'program_financials']
    
    for table in tables:
        count = get_table_count(table)
        if count is not None:
            print(f"  ✅ {table}: {count} записей")
        else:
            print(f"  ⚠️ {table}: не удалось получить количество")


def main():
    """Основная функция миграции"""
    print("=" * 60)
    print("МИГРАЦИЯ ДАННЫХ В SUPABASE")
    print("=" * 60)
    
    # Проверяем конфигурацию
    if not use_supabase():
        print("\n❌ Supabase не настроен!")
        print("Убедитесь, что:")
        print("1. Создан файл .env с SUPABASE_URL и SUPABASE_KEY")
        print("2. USE_LOCAL_STORAGE=false")
        print("\nИли настройте Streamlit secrets для production")
        sys.exit(1)
    
    # Тестируем подключение
    print("\n🔌 Тестирование подключения к Supabase...")
    if not test_connection():
        print("❌ Не удалось подключиться к Supabase")
        print("Проверьте credentials и выполните SQL setup скрипт")
        sys.exit(1)
    
    print("✅ Подключение к Supabase успешно")
    
    # Создаем backup
    backup_dir = backup_local_files()
    
    # Подтверждение от пользователя
    print("\n⚠️  ВНИМАНИЕ: Миграция заменит все существующие данные в Supabase!")
    response = input("Продолжить? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Миграция отменена")
        sys.exit(0)
    
    # Выполняем миграцию
    results = {
        'kpi_history': migrate_kpi_history(),
        'campaigns': migrate_campaigns(),
        'collection_history': migrate_collection_history(),
        'program_financials': migrate_program_financials()
    }
    
    # Проверка
    verify_migration()
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ МИГРАЦИИ")
    print("=" * 60)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for table, success in results.items():
        status = "✅ Успешно" if success else "❌ Ошибка"
        print(f"  {table}: {status}")
    
    print(f"\nУспешно: {success_count}/{total_count}")
    print(f"Backup создан в: {backup_dir}")
    
    if success_count == total_count:
        print("\n🎉 Миграция завершена успешно!")
        print("\nТеперь вы можете:")
        print("1. Запустить приложение: streamlit run main.py")
        print("2. Убедиться, что USE_LOCAL_STORAGE=false в .env")
        print("3. Проверить, что данные загружаются из Supabase")
    else:
        print("\n⚠️  Миграция завершена с ошибками")
        print("Проверьте логи выше для деталей")


if __name__ == "__main__":
    main()
