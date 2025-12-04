"""
Модуль управления финансовыми данными программ
Отвечает за хранение, загрузку и расчеты финансовых показателей программ
Поддерживает Supabase (облако) и pickle (локальное хранилище)
"""

import pandas as pd
import pickle
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from calendar import month_name

# Импорт Supabase manager
try:
    from .supabase_manager import (
        use_supabase,
        supabase_to_dataframe,
        supabase_insert,
        supabase_update,
        supabase_upsert,
        supabase_delete,
        supabase_select,
        dataframe_to_supabase,
        replace_table_data
    )
    SUPABASE_MODULE_AVAILABLE = True
except ImportError:
    SUPABASE_MODULE_AVAILABLE = False
    print("⚠️ Supabase manager not available, using local pickle storage")


# Путь к файлу хранения финансовых данных
FINANCIALS_FILE = "data/program_financials.pkl"

# Список программ
PROGRAMS = [
    "Верь в себя - Краснодар",
    "Верь в себя - Крымск", 
    "Нужна помощь",
    "ЯЖивой",
    "Уставная деятельность"
]


def ensure_data_directory():
    """Создает директорию data, если её нет"""
    os.makedirs("data", exist_ok=True)


def create_empty_financials_df() -> pd.DataFrame:
    """Создает пустой DataFrame для финансовых данных с правильной структурой"""
    return pd.DataFrame(columns=[
        'record_id',      # Уникальный ID записи
        'program',        # Название программы
        'year',           # Год (int)
        'month',          # Месяц (int, 1-12)
        'income',         # Доходы (руб.)
        'expenses',       # Расходы (руб.)
        'created_at',     # Дата создания записи
        'updated_at',     # Дата последнего обновления
        'note'            # Примечание
    ])


def load_financials() -> pd.DataFrame:
    """Загружает финансовые данные из Supabase или файла"""
    # Проверяем, используем ли Supabase
    if SUPABASE_MODULE_AVAILABLE and use_supabase():
        try:
            df = supabase_to_dataframe('program_financials', order_by='year.desc,month.desc')
            if not df.empty:
                print(f"✅ Loaded {len(df)} financial records from Supabase")
                return df
            else:
                return create_empty_financials_df()
        except Exception as e:
            print(f"⚠️ Error loading financials from Supabase: {e}")
            # Fallback to local
    
    # Локальное хранилище (pickle)
    ensure_data_directory()
    
    try:
        if os.path.exists(FINANCIALS_FILE):
            with open(FINANCIALS_FILE, 'rb') as f:
                df = pickle.load(f)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return df
    except Exception as e:
        print(f"Ошибка загрузки финансовых данных: {e}")
    
    return create_empty_financials_df()


def save_financials(df: pd.DataFrame) -> bool:
    """Сохраняет финансовые данные в Supabase или файл"""
    # Проверяем, используем ли Supabase
    if SUPABASE_MODULE_AVAILABLE and use_supabase():
        try:
            df_to_save = df.copy()
            if 'id' in df_to_save.columns:
                df_to_save = df_to_save.drop(columns=['id'])
            
            # ИСПРАВЛЕНИЕ: Используем replace_table_data вместо dataframe_to_supabase
            # Это удаляет все старые записи перед вставкой новых, предотвращая дубликаты
            success = replace_table_data(df_to_save, 'program_financials')
            if success:
                print(f"✅ Saved {len(df)} financial records to Supabase")
                return True
        except Exception as e:
            print(f"⚠️ Error saving financials to Supabase: {e}")
            # Fallback to local
    
    # Локальное хранилище (pickle)
    ensure_data_directory()
    try:
        with open(FINANCIALS_FILE, 'wb') as f:
            pickle.dump(df, f)
        return True
    except Exception as e:
        print(f"Ошибка сохранения финансовых данных: {e}")
        return False


def generate_record_id() -> str:
    """Генерирует уникальный ID записи"""
    return f"FIN_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def calculate_profitability(income: float, expenses: float) -> float:
    """
    Рассчитывает окупаемость: (доходы - расходы) / расходы * 100
    Возвращает процент окупаемости
    """
    if expenses <= 0:
        return 0.0
    return ((income - expenses) / expenses) * 100


def add_financial_record(
    program: str,
    year: int,
    month: int,
    income: float,
    expenses: float,
    note: str = ""
) -> Dict[str, Any]:
    """
    Добавляет новую финансовую запись
    Если запись за этот месяц уже существует, обновляет её
    
    Returns:
        Dict с результатом: {'success': bool, 'record_id': str, 'message': str, 'profitability': float}
    """
    try:
        df = load_financials()
        
        # Проверка на существование записи за этот период
        existing = df[
            (df['program'] == program) & 
            (df['year'] == year) & 
            (df['month'] == month)
        ]
        
        profitability = calculate_profitability(income, expenses)
        
        if not existing.empty:
            # Обновляем существующую запись
            idx = existing.index[0]
            df.loc[idx, 'income'] = income
            df.loc[idx, 'expenses'] = expenses
            df.loc[idx, 'updated_at'] = datetime.now()
            df.loc[idx, 'note'] = note
            
            record_id = df.loc[idx, 'record_id']
            
            if save_financials(df):
                return {
                    'success': True,
                    'record_id': record_id,
                    'message': f'Данные за {month_name[month]} {year} обновлены',
                    'profitability': profitability,
                    'updated': True
                }
        else:
            # Создаем новую запись
            record_id = generate_record_id()
            
            new_record = pd.DataFrame([{
                'record_id': record_id,
                'program': program,
                'year': year,
                'month': month,
                'income': income,
                'expenses': expenses,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'note': note
            }])
            
            df = pd.concat([df, new_record], ignore_index=True)
            
            if save_financials(df):
                return {
                    'success': True,
                    'record_id': record_id,
                    'message': f'Данные за {month_name[month]} {year} добавлены',
                    'profitability': profitability,
                    'updated': False
                }
        
        return {
            'success': False,
            'record_id': None,
            'message': 'Ошибка сохранения данных',
            'profitability': 0
        }
            
    except Exception as e:
        return {
            'success': False,
            'record_id': None,
            'message': f'Ошибка добавления записи: {str(e)}',
            'profitability': 0
        }


def get_financial_record(program: str, year: int, month: int) -> Optional[pd.Series]:
    """Возвращает финансовую запись за конкретный месяц"""
    df = load_financials()
    
    if df.empty:
        return None
    
    result = df[
        (df['program'] == program) & 
        (df['year'] == year) & 
        (df['month'] == month)
    ]
    
    if result.empty:
        return None
    
    return result.iloc[0]


def get_latest_financial_record(program: str) -> Optional[Tuple[pd.Series, int, int]]:
    """
    Возвращает последнюю доступную финансовую запись для программы
    
    Returns:
        Tuple[pd.Series, year, month] или None если записей нет
    """
    df = load_financials()
    
    if df.empty:
        return None
    
    program_data = df[df['program'] == program]
    
    if program_data.empty:
        return None
    
    # Сортируем по году и месяцу в порядке убывания
    program_data = program_data.sort_values(['year', 'month'], ascending=False)
    latest = program_data.iloc[0]
    
    return latest, int(latest['year']), int(latest['month'])


def get_financial_data_with_fallback(
    program: str, 
    target_year: int, 
    target_month: int
) -> Dict[str, Any]:
    """
    Получает финансовые данные за указанный месяц
    Если данных нет, возвращает последние доступные данные с предупреждением
    
    Returns:
        Dict с полями: 
        - 'found': bool - найдены ли данные за целевой месяц
        - 'year': int - год данных
        - 'month': int - месяц данных
        - 'income': float
        - 'expenses': float
        - 'profitability': float
        - 'note': str
        - 'warning': str - предупреждение, если используется fallback
    """
    # Пытаемся получить данные за целевой месяц
    record = get_financial_record(program, target_year, target_month)
    
    if record is not None:
        # Данные найдены
        return {
            'found': True,
            'year': target_year,
            'month': target_month,
            'income': float(record['income']),
            'expenses': float(record['expenses']),
            'profitability': calculate_profitability(record['income'], record['expenses']),
            'note': str(record.get('note', '')),
            'warning': None
        }
    
    # Данных за целевой месяц нет, ищем последние доступные
    latest = get_latest_financial_record(program)
    
    if latest is None:
        # Нет данных вообще
        return {
            'found': False,
            'year': target_year,
            'month': target_month,
            'income': 0.0,
            'expenses': 0.0,
            'profitability': 0.0,
            'note': '',
            'warning': f'Нет финансовых данных для программы "{program}"'
        }
    
    # Возвращаем последние доступные данные с предупреждением
    record, latest_year, latest_month = latest
    
    return {
        'found': False,
        'year': latest_year,
        'month': latest_month,
        'income': float(record['income']),
        'expenses': float(record['expenses']),
        'profitability': calculate_profitability(record['income'], record['expenses']),
        'note': str(record.get('note', '')),
        'warning': f'Данные за {month_name[target_month]} {target_year} не найдены. Показаны данные за {month_name[latest_month]} {latest_year}.'
    }


def get_program_history(program: str) -> pd.DataFrame:
    """Возвращает историю финансовых данных программы"""
    df = load_financials()
    
    if df.empty:
        return create_empty_financials_df()
    
    history = df[df['program'] == program].copy()
    
    # Сортируем по году и месяцу
    if not history.empty:
        history = history.sort_values(['year', 'month'], ascending=False)
        # Добавляем вычисляемое поле окупаемости
        history['profitability'] = history.apply(
            lambda row: calculate_profitability(row['income'], row['expenses']), 
            axis=1
        )
    
    return history


def delete_financial_record(program: str, year: int, month: int) -> Dict[str, Any]:
    """Удаляет финансовую запись"""
    try:
        df = load_financials()
        
        initial_len = len(df)
        
        df = df[~(
            (df['program'] == program) & 
            (df['year'] == year) & 
            (df['month'] == month)
        )]
        
        if len(df) < initial_len:
            if save_financials(df):
                return {
                    'success': True,
                    'message': f'Запись за {month_name[month]} {year} удалена'
                }
        
        return {
            'success': False,
            'message': 'Запись не найдена'
        }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Ошибка удаления: {str(e)}'
        }


def get_aggregated_financials(year: int, month: int) -> Dict[str, Dict[str, float]]:
    """
    Возвращает агрегированные финансовые данные для "Верь в себя - Общие"
    и отдельно для всех программ за указанный месяц
    
    Returns:
        Dict с данными по каждой программе, включая агрегированные "Верь в себя - Общие"
    """
    df = load_financials()
    
    result = {}
    
    if df.empty:
        return result
    
    # Получаем данные за указанный месяц
    month_data = df[(df['year'] == year) & (df['month'] == month)]
    
    # Агрегируем данные по центрам "Верь в себя"
    vs_krasnrodar = month_data[month_data['program'] == 'Верь в себя - Краснодар']
    vs_krymsk = month_data[month_data['program'] == 'Верь в себя - Крымск']
    
    # Суммируем для общих показателей
    vs_total_income = (
        vs_krasnrodar['income'].sum() if not vs_krasnrodar.empty else 0
    ) + (
        vs_krymsk['income'].sum() if not vs_krymsk.empty else 0
    )
    
    vs_total_expenses = (
        vs_krasnrodar['expenses'].sum() if not vs_krasnrodar.empty else 0
    ) + (
        vs_krymsk['expenses'].sum() if not vs_krymsk.empty else 0
    )
    
    # Добавляем агрегированные данные
    result['Верь в себя - Общие'] = {
        'income': vs_total_income,
        'expenses': vs_total_expenses,
        'profitability': calculate_profitability(vs_total_income, vs_total_expenses)
    }
    
    # Добавляем данные по каждой программе
    for program in PROGRAMS:
        program_data = month_data[month_data['program'] == program]
        if not program_data.empty:
            record = program_data.iloc[0]
            result[program] = {
                'income': float(record['income']),
                'expenses': float(record['expenses']),
                'profitability': calculate_profitability(record['income'], record['expenses'])
            }
    
    return result


def get_program_financials_for_period(
    program: str,
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    Получает финансовые данные программы за указанный период
    
    Args:
        program: название программы
        start_date: начало периода
        end_date: конец периода
    
    Returns:
        DataFrame с колонками: year, month, income, expenses, profitability
        Отсортирован по году и месяцу
    """
    df = load_financials()
    
    if df.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Фильтруем по программе
    program_data = df[df['program'] == program].copy()
    
    if program_data.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Фильтруем по периоду
    # Создаем временную колонку с датами для фильтрации
    program_data['date_temp'] = pd.to_datetime(
        program_data['year'].astype(str) + '-' + program_data['month'].astype(str) + '-01'
    )
    
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)
    
    # Фильтруем по периоду (включаем месяцы, где первое число попадает в диапазон)
    period_data = program_data[
        (program_data['date_temp'] >= start_dt.replace(day=1)) & 
        (program_data['date_temp'] <= end_dt)
    ].copy()
    
    if period_data.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Рассчитываем окупаемость
    period_data['profitability'] = period_data.apply(
        lambda row: calculate_profitability(row['income'], row['expenses']),
        axis=1
    )
    
    # Сортируем по году и месяцу
    period_data = period_data.sort_values(['year', 'month'])
    
    # Возвращаем только нужные колонки
    return period_data[['year', 'month', 'income', 'expenses', 'profitability']].reset_index(drop=True)


def get_aggregated_financials_for_period(
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    Получает агрегированные финансовые данные для "Верь в себя - Общие" за период
    
    Args:
        start_date: начало периода
        end_date: конец периода
    
    Returns:
        DataFrame с колонками: year, month, income, expenses, profitability
    """
    df = load_financials()
    
    if df.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Фильтруем данные по периоду
    df['date_temp'] = pd.to_datetime(
        df['year'].astype(str) + '-' + df['month'].astype(str) + '-01'
    )
    
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)
    
    period_data = df[
        (df['date_temp'] >= start_dt.replace(day=1)) & 
        (df['date_temp'] <= end_dt)
    ].copy()
    
    if period_data.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Фильтруем только центры Верь в себя
    vs_data = period_data[
        (period_data['program'] == 'Верь в себя - Краснодар') |
        (period_data['program'] == 'Верь в себя - Крымск')
    ]
    
    if vs_data.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Группируем по году и месяцу, суммируя доходы и расходы
    aggregated = vs_data.groupby(['year', 'month']).agg({
        'income': 'sum',
        'expenses': 'sum'
    }).reset_index()
    
    # Рассчитываем окупаемость
    aggregated['profitability'] = aggregated.apply(
        lambda row: calculate_profitability(row['income'], row['expenses']),
        axis=1
    )
    
    # Сортируем по году и месяцу
    aggregated = aggregated.sort_values(['year', 'month'])
    
    return aggregated.reset_index(drop=True)


def get_company_wide_financials_for_period(
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    Получает агрегированные финансовые данные по ВСЕЙ компании за период
    Включает все программы + уставную деятельность
    
    Args:
        start_date: начало периода
        end_date: конец периода
    
    Returns:
        DataFrame с колонками: year, month, income, expenses, profitability
    """
    df = load_financials()
    
    if df.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Фильтруем данные по периоду
    df['date_temp'] = pd.to_datetime(
        df['year'].astype(str) + '-' + df['month'].astype(str) + '-01'
    )
    
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)
    
    period_data = df[
        (df['date_temp'] >= start_dt.replace(day=1)) & 
        (df['date_temp'] <= end_dt)
    ].copy()
    
    if period_data.empty:
        return pd.DataFrame(columns=['year', 'month', 'income', 'expenses', 'profitability'])
    
    # Группируем по году и месяцу, суммируя доходы и расходы ПО ВСЕМ программам
    # Это включает все программы из PROGRAMS + уставную деятельность (если есть)
    aggregated = period_data.groupby(['year', 'month']).agg({
        'income': 'sum',
        'expenses': 'sum'
    }).reset_index()
    
    # Рассчитываем окупаемость
    aggregated['profitability'] = aggregated.apply(
        lambda row: calculate_profitability(row['income'], row['expenses']),
        axis=1
    )
    
    # Сортируем по году и месяцу
    aggregated = aggregated.sort_values(['year', 'month'])
    
    return aggregated.reset_index(drop=True)

