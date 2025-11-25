#!/usr/bin/env python
"""
Скрипт для проверки функции filter_data_by_period
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

# --- НАСТРОЙКИ И КОНСТАНТЫ ---
# Полная структура KPI
KPI_STRUCTURE = {
    "SMM (Вовлеченность)": {
        "SMM.ER": "ER (Engagement Rate), % [KPI.СММ.1]",
        "SMM.SHARE": "Share Rate (Репосты), %",
        "SMM.CTR": "CTR (Клики на сайт), %"
    },
    "SMM (Фандрайзинг)": {
        "SMM.DCR": "DCR (Конверсия в донат), %",
        "SMM.MONEY": "Сумма сбора SMM, руб. (Часть KPI.ФР.1)"
    },
    "Программы": {
        "KPI.ВС.1": "Заполняемость центров (Верь в себя), %",
        "KPI.НП.1": "Своевременность решений (Нужна помощь), %",
        "KPI.НП.2": "Объем адресной помощи, руб.",
        "KPI.ЯЖ.1": "Мониторинг цел. использования (ЯЖивой), %"
    },
    "Финансы": {
        "KPI.ФР.1_ОБЩИЙ": "Выполнение общего плана фандрайзинга, %",
        "KPI.ФИН.1": "Соблюдение бюджета (отклонение), %",
        "KPI.ГР.1": "Грантовая эффективность (заявки/отчеты)"
    },
    "HR и Администрирование": {
        "KPI.HR.1": "Просроченные HR-задачи (Адаптация/Развитие)",
        "KPI.ВЛ.1": "Прирост базы волонтеров, %",
        "KPI.ДЕЛ.1": "Своевременность документооборота, %",
        "KPI.АДМ.1": "Обработка звонков и посетителей, %"
    }
}

# Определение колонок для создания пустой, но структурированной DF
REQUIRED_COLUMNS = ["Дата_Начала", "Неделя_Год", "Промежуток_Дат", "Категория", "KPI_ID", "Название", "Минимум", "Цель",
                    "Факт", "Комментарий"]


# --- ФУНКЦИЯ ДЛЯ РАСЧЕТА НЕДЕЛИ ---
def get_week_info(d: date):
    """Возвращает ID недели (YYYY-WXX) и диапазон дат (DD.MM.YYYY - DD.MM.YYYY)."""
    start_of_week = d - timedelta(days=d.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    week_year_id = start_of_week.strftime('%Y-W%W')
    date_range = f"{start_of_week.strftime('%d.%m.%Y')} - {end_of_week.strftime('%d.%m.%Y')}"
    return start_of_week, week_year_id, date_range


# --- ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ ---
def generate_mock_data():
    data = []
    end_date = datetime.now()
    start_date = datetime(end_date.year, 1, 1)

    categories_map = {
        "SMM.MONEY": ("Сумма сбора SMM, руб. (Часть KPI.ФР.1)", 40000.0, 60000.0),
        "SMM.ER": ("ER (Engagement Rate), % [KPI.СММ.1]", 2.5, 4.0),
        "SMM.DCR": ("DCR (Конверсия в донат), %", 1.0, 2.0),
        "SMM.SHARE": ("Share Rate (Репосты), %", 0.5, 1.0),
        "KPI.ВС.1": ("Заполняемость центров (Верь в себя), %", 85.0, 95.0),
        "KPI.ФИН.1": ("Соблюдение бюджета (отклонение), %", 5.0, 0.0),
        "KPI.ФР.1_ОБЩИЙ": ("Выполнение общего плана фандрайзинга, %", 80.0, 100.0),
    }

    current_date = start_date
    while current_date <= end_date:
        # Вносим данные за каждый понедельник
        if current_date.weekday() == 0 or current_date == start_date:
            start_of_week, week_id, date_range_str = get_week_info(current_date.date())

            for kpi_id, (name, min_val, target_val) in categories_map.items():
                if np.random.random() > 0.1:

                    if kpi_id == "KPI.ФИН.1":
                        fact_val = abs(np.random.normal(2, 2))
                    elif 'MONEY' in kpi_id:
                        fact_val = np.random.uniform(min_val * 0.8, target_val * 1.2)
                    else:
                        fact_val = np.random.normal(target_val, target_val * 0.15)

                    fact_val = max(0, fact_val)

                    category = next((cat_name for cat_name, kpis in KPI_STRUCTURE.items() if kpi_id in kpis), "Прочее")

                    data.append({
                        "Дата_Начала": start_of_week,
                        "Неделя_Год": week_id,
                        "Промежуток_Дат": date_range_str,
                        "Категория": category,
                        "KPI_ID": kpi_id,
                        "Название": name,
                        "Минимум": min_val,
                        "Цель": target_val,
                        "Факт": round(fact_val, 2),
                        "Комментарий": ""
                    })

        current_date += timedelta(days=7)

    df = pd.DataFrame(data)
    # Гарантируем, что даты - это Python date объекты
    df['Дата_Начала'] = pd.to_datetime(df['Дата_Начала']).dt.date
    return df


# --- ФУНКЦИЯ ПРИНУДИТЕЛЬНОЙ ОЧИСТКИ ДАННЫХ ---
def clean_data_types(df):
    """Обеспечивает корректность типов данных и удаляет только критически некорректные строки.
    Не удаляем строки при отсутствии одного из числовых полей — это было причиной потери всей БД.
    """
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Если вход пуст — возвращаем корректно структурированную пустую DF
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Приведение даты к Python date object (если есть колонка)
    if 'Дата_Начала' in df.columns:
        df['Дата_Начала'] = pd.to_datetime(df['Дата_Начала'], errors='coerce').dt.date
    else:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Приведение числовых колонок к float, но не удаляем строки из-за NaN в них
    numerical_cols = ['Минимум', 'Цель', 'Факт']
    for col in numerical_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Удаляем только строки, где отсутствует KPI_ID или Название — эти поля критичны.
    df = df.dropna(subset=['KPI_ID', 'Название'])

    # Сбрасываем индекс (чтобы избежать проблем с неправильными индексами после редактирования)
    df = df.reset_index(drop=True)

    # Убедимся, что все нужные колонки присутствуют (добавим отсутствующие с NaN/пустотой)
    for c in REQUIRED_COLUMNS + ['Дата_Начала_DT', 'Период']:
        if c not in df.columns:
            df[c] = pd.NA

    return df


def filter_data_by_period(df, period_type, selected_month_str=None):
    """Фильтрует и группирует данные: по месяцам (для Года) или по неделям (для Месяца)."""
    df = df.copy()

    # Если данные уже очищены функцией clean_data_types, они должны быть в формате Python date objects.
    # Преобразование в datetime64[ns] для Pandas-агрегации.
    df['Дата_Начала_DT'] = pd.to_datetime(df['Дата_Начала'], errors='coerce')
    numerical_cols = ['Минимум', 'Цель', 'Факт']

    print(f"Фильтрация: после создания 'Дата_Начала_DT', тип: {df['Дата_Начала_DT'].dtype}")
    print(f"Фильтрация: первые значения 'Дата_Начала_DT': {df['Дата_Начала_DT'].head()}")
    
    # КРИТИЧЕСКИЙ ФИЛЬТР: Отбрасываем строки, где нет даты или числа
    df = df.dropna(subset=['Дата_Начала_DT', 'Название'])
    if df.empty:
        print("Фильтрация: DataFrame пуст после фильтрации по дате и названию")
        return pd.DataFrame()

    print(f"Фильтрация: после фильтрации NaN, осталось строк: {len(df)}")
    
    # 2. Фильтрация и группировка
    if period_type == "Год (по месяцам)":

        # Ключ для группировки и сортировки (YYYY-MM)
        df['Period_Key'] = df['Дата_Начала_DT'].dt.strftime('%Y-%m')

        # Метка для оси X (Январь 2024)
        df['Период_Display'] = df['Дата_Начала_DT'].dt.strftime('%B %Y')

        # Группируем по ключу периода и Названию KPI
        df_grouped = df.groupby(['Period_Key', 'Период_Display', 'Название'])[numerical_cols].mean().reset_index()

        # Сортируем по надежному строковому ключу
        df_grouped = df_grouped.sort_values('Period_Key')
        df_grouped['Период'] = df_grouped['Период_Display']  # Финальная колонка метки


    else:  # Месяц (по неделям)
        if selected_month_str is None:
            print("Фильтрация: нет выбранного месяца для фильтрации по неделям")
            return pd.DataFrame()

        y, m = map(int, selected_month_str.split('-'))
        print(f"Фильтрация: фильтруем по году {y}, месяцу {m}")

        # Фильтрация по году и месяцу
        df_filtered = df[(df['Дата_Начала_DT'].dt.year == y) & (df['Дата_Начала_DT'].dt.month == m)].copy()

        if df_filtered.empty:
            print(f"Фильтрация: нет данных за {y}-{m:02d}")
            return pd.DataFrame()

        # Группировка по уже существующим надежным строковым колонкам
        df_grouped = df_filtered.groupby(['Неделя_Год', 'Промежуток_Дат', 'Название'])[
            numerical_cols].mean().reset_index()
        df_grouped = df_grouped.sort_values('Неделя_Год')
        df_grouped['Период'] = df_grouped['Промежуток_Дат']

    # Возвращаем только необходимые для графика колонки
    return df_grouped[['Название', 'Минимум', 'Цель', 'Факт', 'Период']]


# --- ОСНОВНОЙ КОД ---
print("Генерируем тестовые данные...")
df = generate_mock_data()
print(f"Сгенерировано {len(df)} записей")
print(f"Столбцы: {list(df.columns)}")
print(f"Значения 'Дата_Начала': {df['Дата_Начала'].head()}")

print("\nПрименяем clean_data_types...")
df_cleaned = clean_data_types(df)
print(f"После очистки: {len(df_cleaned)} записей")
print(f"Столбцы: {list(df_cleaned.columns)}")
print(f"Значения 'Дата_Начала_DT': {df_cleaned['Дата_Начала_DT'].head()}")

print("\nПроверяем фильтрацию по году...")
df_yearly = filter_data_by_period(df_cleaned, "Год (по месяцам)")
print(f"Фильтрация по году: {len(df_yearly)} записей")
print(f"Колонки результата: {list(df_yearly.columns) if not df_yearly.empty else 'DataFrame пуст'}")

print("\nПроверяем фильтрацию по месяцу...")
# Определим доступный месяц из данных
if not df_cleaned.empty:
    available_months = df_cleaned['Дата_Начала'].dt.strftime('%Y-%m').unique()
    print(f"Доступные месяцы: {available_months}")
    
    for month in available_months:
        print(f"\nТестируем месяц: {month}")
        df_monthly = filter_data_by_period(df_cleaned, "Месяц (по неделям)", month)
        print(f"Фильтрация по месяцу {month}: {len(df_monthly)} записей")
        print(f"Колонки результата: {list(df_monthly.columns) if not df_monthly.empty else 'DataFrame пуст'}")
        if not df_monthly.empty:
            print(f"Пример записей: {df_monthly.head()}")
else:
    print("Нет данных для фильтрации по месяцу")