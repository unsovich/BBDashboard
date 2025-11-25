#!/usr/bin/env python
"""
Скрипт для проверки функции clean_data_types в приложении дашборда
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
    print(f"Вход в clean_data_types: тип df = {type(df)}")
    if not isinstance(df, pd.DataFrame):
        print("Возвращаем пустой DataFrame с REQUIRED_COLUMNS")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Если вход пуст — возвращаем корректно структурированную пустую DF
    if df.empty:
        print("DataFrame пустой, возвращаем структурированный пустой DataFrame")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    print(f"Столбцы до обработки: {list(df.columns)}")
    print(f"Тип 'Дата_Начала' до преобразования: {df['Дата_Начала'].dtype}")
    print(f"Значения 'Дата_Начала' до преобразования: {df['Дата_Начала'].head()}")

    # Приведение даты к Python date object (если есть колонка)
    if 'Дата_Начала' in df.columns:
        df['Дата_Начала'] = pd.to_datetime(df['Дата_Начала'], errors='coerce').dt.date
        print(f"Значения 'Дата_Начала' после преобразования: {df['Дата_Начала'].head()}")
    else:
        print("Нет столбца 'Дата_Начала', возвращаем пустой DataFrame")
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
            print(f"Добавлен столбец {c} со значениями pd.NA")

    print(f"Столбцы после обработки: {list(df.columns)}")
    print(f"Тип 'Дата_Начала_DT' после добавления: {df['Дата_Начала_DT'].dtype}")
    print(f"Значения 'Дата_Начала_DT' после добавления: {df['Дата_Начала_DT'].head()}")

    return df


# --- ОСНОВНОЙ КОД ---
print("Генерируем тестовые данные...")
df = generate_mock_data()
print(f"Сгенерировано {len(df)} записей")
print(f"Тип 'Дата_Начала' до clean_data_types: {df['Дата_Начала'].dtype}")
print(f"Значения 'Дата_Начала' до clean_data_types: {df['Дата_Начала'].head()}")

print("\nПроверяем функцию clean_data_types...")
df_cleaned = clean_data_types(df)
print(f"После очистки: {len(df_cleaned)} записей")
print(f"Тип 'Дата_Начала_DT' после clean_data_types: {df_cleaned['Дата_Начала_DT'].dtype}")
print(f"Значения 'Дата_Начала_DT' после clean_data_types: {df_cleaned['Дата_Начала_DT'].head()}")
print(f"Значения 'Дата_Начала' после clean_data_types: {df_cleaned['Дата_Начала'].head()}")