import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np
import pickle
import os

import sys
import os

# Ensure current directory is in path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Импорт модулей мониторинга кампаний
try:
    from modules.campaign_data import load_campaigns, save_campaigns
    from modules.campaign_analytics import compare_channels
    from modules.campaign_viz import (
        render_campaign_summary_table,
        render_channel_comparison
    )
    from modules.campaign_ui import (
        render_campaign_input_form,
        render_campaign_editor,
        render_campaign_detail_view,
        export_campaign_report,
        render_collection_update_form,
        render_multi_channel_dashboard
    )
    CAMPAIGNS_MODULE_AVAILABLE = True
except ImportError as e:
    CAMPAIGNS_MODULE_AVAILABLE = False
    CAMPAIGNS_ERROR = str(e)
    print(f"Campaign modules not available: {e}")

# Импорт модуля финансов программ
try:
    from modules.program_financials import (
        load_financials,
        save_financials,
        add_financial_record,
        get_financial_data_with_fallback,
        get_program_history,
        get_aggregated_financials,
        calculate_profitability,
        PROGRAMS
    )
    FINANCIALS_MODULE_AVAILABLE = True
except ImportError as e:
    FINANCIALS_MODULE_AVAILABLE = False
    FINANCIALS_ERROR = str(e)
    print(f"Program financials module not available: {e}")


# --- НАСТРОЙКИ И КОНСТАНТЫ ---
st.set_page_config(page_title="АНО «Синяя птица» - KPI Monitor v2.17 (ИСПРАВЛЕНА ПОТЕРЯ ДАННЫХ)", layout="wide")

# Файл для автосохранения
BACKUP_FILE = "kpi_backup.pkl"

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
    "Верь в себя - Краснодар (Процессы)": {
        "KPI.ВС.КРАСНОДАР.PROC.1": "Количество проведенных занятий (факт/план)",
        "KPI.ВС.КРАСНОДАР.PROC.2": "Количество обслуженных благополучателей",
        "KPI.ВС.КРАСНОДАР.PROC.3": "Коэффициент конверсии обращений",
        "KPI.ВС.КРАСНОДАР.PROC.4": "Уровень удержания благополучателей"
    },
    "Верь в себя - Краснодар (Соц. воздействие)": {
        "KPI.ВС.КРАСНОДАР.SOC.1": "Индекс достижения социальной реабилитации",
        "KPI.ВС.КРАСНОДАР.SOC.2": "Количество благополучателей, прошедших профориентацию",
        "KPI.ВС.КРАСНОДАР.SOC.3": "Уровень удовлетворенности благополучателей"
    },
    "Верь в себя - Краснодар (Финансы)": {
        "KPI.ВС.КРАСНОДАР.FIN.1": "Стоимость оказания услуг на 1 благополучателя",
        "KPI.ВС.КРАСНОДАР.FIN.2": "Отклонение от сметы",
        "KPI.ВС.КРАСНОДАР.FIN.3": "Коэффициент привлечения натуральной помощи"
    },
    "Верь в себя - Крымск (Процессы)": {
        "KPI.ВС.КРЫМСК.PROC.1": "Количество проведенных занятий (факт/план)",
        "KPI.ВС.КРЫМСК.PROC.2": "Количество обслуженных благополучателей",
        "KPI.ВС.КРЫМСК.PROC.3": "Коэффициент конверсии обращений",
        "KPI.ВС.КРЫМСК.PROC.4": "Уровень удержания благополучателей"
    },
    "Верь в себя - Крымск (Соц. воздействие)": {
        "KPI.ВС.КРЫМСК.SOC.1": "Индекс достижения социальной реабилитации",
        "KPI.ВС.КРЫМСК.SOC.2": "Количество благополучателей, прошедших профориентацию",
        "KPI.ВС.КРЫМСК.SOC.3": "Уровень удовлетворенности благополучателей"
    },
    "Верь в себя - Крымск (Финансы)": {
        "KPI.ВС.КРЫМСК.FIN.1": "Стоимость оказания услуг на 1 благополучателя",
        "KPI.ВС.КРЫМСК.FIN.2": "Отклонение от сметы",
        "KPI.ВС.КРЫМСК.FIN.3": "Коэффициент привлечения натуральной помощи"
    },
    "Верь в себя - Общие (Процессы)": {
        "KPI.ВС.ОБЩИЕ.PROC.1": "Количество проведенных занятий (факт/план)",
        "KPI.ВС.ОБЩИЕ.PROC.2": "Количество обслуженных благополучателей",
        "KPI.ВС.ОБЩИЕ.PROC.3": "Коэффициент конверсии обращений",
        "KPI.ВС.ОБЩИЕ.PROC.4": "Уровень удержания благополучателей"
    },
    "Верь в себя - Общие (Соц. воздействие)": {
        "KPI.ВС.ОБЩИЕ.SOC.1": "Индекс достижения социальной реабилитации",
        "KPI.ВС.ОБЩИЕ.SOC.2": "Количество благополучателей, прошедших профориентацию",
        "KPI.ВС.ОБЩИЕ.SOC.3": "Уровень удовлетворенности благополучателей"
    },
    "Верь в себя - Общие (Финансы)": {
        "KPI.ВС.ОБЩИЕ.FIN.1": "Стоимость оказания услуг на 1 благополучателя",
        "KPI.ВС.ОБЩИЕ.FIN.2": "Отклонение от сметы",
        "KPI.ВС.ОБЩИЕ.FIN.3": "Коэффициент привлечения натуральной помощи"
    },
    "Нужна помощь (Процессы)": {
        "KPI.НП.PROC.1": "Коэффициент своевременности рассмотрения заявок",
        "KPI.НП.PROC.2": "Коэффициент полноты документации (одобренные заявки)",
        "KPI.НП.PROC.3": "Коэффициент доказательности отказа",
        "KPI.НП.PROC.4": "Коэффициент соблюдения процедуры"
    },
    "Нужна помощь (Результаты)": {
        "KPI.НП.RES.1": "Объем предоставленной помощи (денежная форма)",
        "KPI.НП.RES.2": "Объем предоставленной помощи (натуральная форма)",
        "KPI.НП.RES.3": "Количество обслуженных благополучателей"
    },
    "Нужна помощь (Соц. воздействие)": {
        "KPI.НП.SOC.1": "Индекс целевого использования средств",
        "KPI.НП.SOC.2": "Своевременность предоставления помощи",
        "KPI.НП.SOC.3": "Доля исключительных случаев в общем объеме помощи"
    },
    "ЯЖивой (Процессы)": {
        "KPI.ЯЖ.PROC.1": "Коэффициент коллегиальности",
        "KPI.ЯЖ.PROC.2": "Коэффициент оформления помощи",
        "KPI.ЯЖ.PROC.3": "Коэффициент отклонения по недостоверности",
        "KPI.ЯЖ.PROC.4": "Коэффициент своевременности уведомления"
    },
    "ЯЖивой (Результаты)": {
        "KPI.ЯЖ.RES.1": "Количество обслуженных благополучателей",
        "KPI.ЯЖ.RES.2": "Объем предоставленной целевой помощи",
        "KPI.ЯЖ.RES.3": "Объем помощи в натуральной форме"
    },
    "ЯЖивой (Соц. воздействие)": {
        "KPI.ЯЖ.SOC.1": "Индекс целевого использования средств",
        "KPI.ЯЖ.SOC.2": "Индекс достижения социальной адаптации",
        "KPI.ЯЖ.SOC.3": "Стоимость комплексной помощи на 1 благополучателя"
    },
    "Корп. Фандрайзинг (Результат)": {
        "KPI.КФ.RES.1": "Объем привлеченных средств, руб.",
        "KPI.КФ.RES.2": "Количество новых партнеров",
        "KPI.КФ.RES.3": "Коэффициент удержания партнеров, %",
        "KPI.КФ.RES.4": "Средний чек сделки, руб.",
        "KPI.КФ.RES.5": "Стоимость привлечения партнера, руб."
    },
    "Корп. Фандрайзинг (Деятельность)": {
        "KPI.КФ.ACT.1": "Количество установленных первых контактов",
        "KPI.КФ.ACT.2": "Количество отправленных предложений",
        "KPI.КФ.ACT.3": "Количество личных встреч с ЛПР",
        "KPI.КФ.ACT.4": "Количество партнеров в работе",
        "KPI.КФ.ACT.5": "Скорость конверсии (дни)"
    },
    "Финансы": {
        "KPI.ФР.1_ОБЩИЙ": "Выполнение общего плана фандрайзинга, %",
        "KPI.ФИН.1": "Соблюдение бюджета (отклонение), %",
        "KPI.ГР.1": "Грантовая эффективность (заявки/отчеты)"
    },
    "Фандрайзинг (Эффективность)": {
        "FR.INPUT.COSTS": "Прямые расходы (Реклама/Бюджет), руб.",
        "FR.INPUT.HOURS": "Трудозатраты персонала, ч.",
        "FR.OUTPUT.FUNDS": "Привлеченные средства (Факт), руб.",
        "FR.OUTPUT.DONORS": "Количество доноров, чел.",
        "FR.CONV.REACH": "Охват (Просмотры), ед.",
        "FR.CONV.ACTIONS": "Целевые действия (Конверсии), ед."
    },
    "HR и Администрирование": {
        "KPI.HR.1": "Просроченные HR-задачи (Адаптация/Развитие)",
        "KPI.ВЛ.1": "Прирост базы волонтеров, %",
        "KPI.ДЕЛ.1": "Своевременность документооборота, %",
        "KPI.АДМ.1": "Обработка звонков и посетителей, %"
    }
}

# Определение колонок для создания пустой, но структурированной DF
REQUIRED_COLUMNS = ["Дата_Начала", "Дата_Окончания", "Неделя_Год", "Промежуток_Дат", "Категория", "KPI_ID", "Название", "Минимум", "Цель",
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
        "KPI.ФИН.1": ("Соблюдение бюджета (отклонение), %", 5.0, 0.0),
        "KPI.ФР.1_ОБЩИЙ": ("Выполнение общего плана фандрайзинга, %", 80.0, 100.0),

        # Верь в себя
        "KPI.ВС.PROC.1": ("Количество проведенных занятий (факт/план)", 40.0, 50.0),
        "KPI.ВС.PROC.2": ("Количество обслуженных благополучателей", 100.0, 120.0),
        "KPI.ВС.PROC.3": ("Коэффициент конверсии обращений", 0.3, 0.5),
        "KPI.ВС.PROC.4": ("Уровень удержания благополучателей", 0.7, 0.85),
        "KPI.ВС.SOC.1": ("Индекс достижения социальной реабилитации", 0.6, 0.8),
        "KPI.ВС.SOC.2": ("Количество благополучателей, прошедших профориентацию", 10.0, 15.0),
        "KPI.ВС.SOC.3": ("Уровень удовлетворенности благополучателей", 4.0, 4.8),
        "KPI.ВС.FIN.1": ("Стоимость оказания услуг на 1 благополучателя", 1500.0, 1200.0),
        "KPI.ВС.FIN.2": ("Отклонение от сметы", 5.0, 0.0),
        "KPI.ВС.FIN.3": ("Коэффициент привлечения натуральной помощи", 0.1, 0.2),

        # Нужна помощь
        "KPI.НП.PROC.1": ("Коэффициент своевременности рассмотрения заявок", 0.8, 0.95),
        "KPI.НП.PROC.2": ("Коэффициент полноты документации (одобренные заявки)", 0.9, 1.0),
        "KPI.НП.PROC.3": ("Коэффициент доказательности отказа", 0.9, 1.0),
        "KPI.НП.PROC.4": ("Коэффициент соблюдения процедуры", 0.95, 1.0),
        "KPI.НП.RES.1": ("Объем предоставленной помощи (денежная форма)", 500000.0, 600000.0),
        "KPI.НП.RES.2": ("Объем предоставленной помощи (натуральная форма)", 100000.0, 150000.0),
        "KPI.НП.RES.3": ("Количество обслуженных благополучателей", 50.0, 70.0),
        "KPI.НП.SOC.1": ("Индекс целевого использования средств", 0.95, 1.0),
        "KPI.НП.SOC.2": ("Своевременность предоставления помощи", 0.85, 0.95),
        "KPI.НП.SOC.3": ("Доля исключительных случаев в общем объеме помощи", 0.05, 0.0),

        # ЯЖивой
        "KPI.ЯЖ.PROC.1": ("Коэффициент коллегиальности", 0.9, 1.0),
        "KPI.ЯЖ.PROC.2": ("Коэффициент оформления помощи", 0.9, 1.0),
        "KPI.ЯЖ.PROC.3": ("Коэффициент отклонения по недостоверности", 0.1, 0.0),
        "KPI.ЯЖ.PROC.4": ("Коэффициент своевременности уведомления", 0.9, 1.0),
        "KPI.ЯЖ.RES.1": ("Количество обслуженных благополучателей", 30.0, 40.0),
        "KPI.ЯЖ.RES.2": ("Объем предоставленной целевой помощи", 300000.0, 400000.0),
        "KPI.ЯЖ.RES.3": ("Объем помощи в натуральной форме", 50000.0, 80000.0),
        "KPI.ЯЖ.SOC.1": ("Индекс целевого использования средств", 0.95, 1.0),
        "KPI.ЯЖ.SOC.2": ("Индекс достижения социальной адаптации", 0.6, 0.8),
        "KPI.ЯЖ.SOC.3": ("Стоимость комплексной помощи на 1 благополучателя", 5000.0, 4500.0),

        # Корп. Фандрайзинг
        "KPI.КФ.RES.1": ("Объем привлеченных средств, руб.", 500000.0, 1000000.0),
        "KPI.КФ.RES.2": ("Количество новых партнеров", 1.0, 5.0),
        "KPI.КФ.RES.3": ("Коэффициент удержания партнеров, %", 70.0, 90.0),
        "KPI.КФ.RES.4": ("Средний чек сделки, руб.", 100000.0, 300000.0),
        "KPI.КФ.RES.5": ("Стоимость привлечения партнера, руб.", 5000.0, 15000.0),
        "KPI.КФ.ACT.1": ("Количество установленных первых контактов", 10.0, 30.0),
        "KPI.КФ.ACT.2": ("Количество отправленных предложений", 5.0, 15.0),
        "KPI.КФ.ACT.3": ("Количество личных встреч с ЛПР", 2.0, 8.0),
        "KPI.КФ.ACT.4": ("Количество партнеров в работе", 15.0, 40.0),
        "KPI.КФ.ACT.5": ("Скорость конверсии (дни)", 10.0, 45.0),

        # Фандрайзинг (Эффективность)
        "FR.INPUT.COSTS": ("Прямые расходы (Реклама/Бюджет), руб.", 5000.0, 10000.0),
        "FR.INPUT.HOURS": ("Трудозатраты персонала, ч.", 10.0, 20.0),
        "FR.OUTPUT.FUNDS": ("Привлеченные средства (Факт), руб.", 50000.0, 100000.0),
        "FR.OUTPUT.DONORS": ("Количество доноров, чел.", 50.0, 100.0),
        "FR.CONV.REACH": ("Охват (Просмотры), ед.", 10000.0, 20000.0),
        "FR.CONV.ACTIONS": ("Целевые действия (Конверсии), ед.", 100.0, 200.0),
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
                    elif 'MONEY' in kpi_id or 'Объем привлеченных средств' in name or 'Средний чек сделки' in name or 'Стоимость привлечения партнера' in name or 'Привлеченные средства' in name or 'Прямые расходы' in name:
                        fact_val = np.random.uniform(min_val * 0.8, target_val * 1.2)
                    elif 'Охват' in name:
                         fact_val = np.random.uniform(min_val * 0.8, target_val * 1.5)
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


# --- ИСПРАВЛЕННАЯ ФУНКЦИЯ ОЧИСТКИ ДАННЫХ ---
def clean_data_types(df):
    """Обеспечивает корректность типов данных БЕЗ удаления строк.
    Только валидация и приведение типов, без dropna().
    """
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Создаем копию для безопасности
    df = df.copy()

    # Приведение даты к Python date object
    if 'Дата_Начала' in df.columns:
        df['Дата_Начала'] = pd.to_datetime(df['Дата_Начала'], errors='coerce').dt.date
    else:
        df['Дата_Начала'] = None

    if 'Дата_Окончания' in df.columns:
        df['Дата_Окончания'] = pd.to_datetime(df['Дата_Окончания'], errors='coerce').dt.date
    else:
        # Если нет даты окончания, считаем её равной дате начала (для старых записей)
        df['Дата_Окончания'] = df['Дата_Начала']

    # Приведение числовых колонок к float (но НЕ удаляем строки с NaN)
    numerical_cols = ['Минимум', 'Цель', 'Факт']
    for col in numerical_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan

    # Заполняем отсутствующие обязательные текстовые поля пустыми строками
    text_cols = ['KPI_ID', 'Название', 'Категория', 'Комментарий', 'Неделя_Год', 'Промежуток_Дат']
    for col in text_cols:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("")

    # Сбрасываем индекс
    df = df.reset_index(drop=True)

    return df


# --- ФУНКЦИЯ СОХРАНЕНИЯ В ФАЙЛ ---
def save_to_file(df):
    """Сохраняет DataFrame в файл бэкапа"""
    try:
        with open(BACKUP_FILE, 'wb') as f:
            pickle.dump(df, f)
    except Exception as e:
        st.error(f"Ошибка сохранения бэкапа: {e}")


# --- ФУНКЦИЯ ЗАГРУЗКИ ИЗ ФАЙЛА ---
def load_from_file():
    """Загружает DataFrame из файла бэкапа"""
    try:
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        st.warning(f"Не удалось загрузить бэкап: {e}")
    return None


# --- ИСПРАВЛЕННАЯ ИНИЦИАЛИЗАЦИЯ SESSION STATE ---
# КРИТИЧЕСКАЯ ЗАЩИТА ОТ ПОТЕРИ ДАННЫХ:
# 1. Сначала проверяем наличие файла бэкапа
# 2. Генерируем mock данные ТОЛЬКО если файла НЕТ ВООБЩЕ
# 3. Если файл есть, но пустой - сохраняем пустой DataFrame (пользователь очистил данные)

if 'kpi_history' not in st.session_state:
    # Пытаемся загрузить из файла
    loaded_data = load_from_file()
    
    if loaded_data is not None:
        # Файл существует и загружен успешно
        # Используем данные из файла даже если они пустые
        st.session_state.kpi_history = loaded_data
        st.session_state.data_source = "loaded_from_file"
    elif os.path.exists(BACKUP_FILE):
        # Файл существует, но не удалось загрузить (поврежден)
        st.warning(f"⚠️ Файл {BACKUP_FILE} поврежден. Создаем резервную копию и начинаем с пустой базы.")
        # Переименовываем поврежденный файл
        backup_corrupted = f"{BACKUP_FILE}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            os.rename(BACKUP_FILE, backup_corrupted)
            st.info(f"Поврежденный файл сохранен как: {backup_corrupted}")
        except:
            pass
        # Начинаем с пустой базы
        st.session_state.kpi_history = pd.DataFrame(columns=REQUIRED_COLUMNS)
        save_to_file(st.session_state.kpi_history)
        st.session_state.data_source = "corrupted_file_recovered"
    else:
        # Файла НЕ СУЩЕСТВУЕТ - это первый запуск
        # ТОЛЬКО в этом случае генерируем mock данные
        st.session_state.kpi_history = generate_mock_data()
        save_to_file(st.session_state.kpi_history)
        st.session_state.data_source = "generated_mock_data"
        st.info("ℹ️ Первый запуск: создана база с тестовыми данными. Вы можете удалить их в разделе 'История (Редактор)'.")
    
    st.session_state.data_initialized = True


# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Убрана автоматическая очистка при каждом обновлении страницы
# Данные НЕ очищаются при каждом рендере


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def aggregate_center_kpis(df, start_date, end_date):
    """
    Агрегирует KPI из центров Краснодар и Крымск в общие показатели.
    Суммирует количественные показатели, усредняет коэффициенты и индексы.
    
    Args:
        df: DataFrame с KPI данными
        start_date: начало периода
        end_date: конец периода
    
    Returns:
        DataFrame с агрегированными данными для категорий "Верь в себя - Общие"
    """
    # Фильтруем данные за период
    df = df.copy()
    df['Дата_Начала_DT'] = pd.to_datetime(df['Дата_Начала'], errors='coerce')
    mask = (df['Дата_Начала_DT'].dt.date >= start_date) & (df['Дата_Начала_DT'].dt.date <= end_date)
    df_period = df.loc[mask]
    
    if df_period.empty:
        return pd.DataFrame()
    
    # Получаем данные по центрам
    krasnodar_data = df_period[df_period['Категория'].str.contains('Краснодар', na=False)]
    krymsk_data = df_period[df_period['Категория'].str.contains('Крымск', na=False)]
    
    aggregated_records = []
    
    # Маппинг KPI для агрегации
    kpi_mappings = {
        'PROC.1': ('Количество проведенных занятий (факт/план)', 'sum'),
        'PROC.2': ('Количество обслуженных благополучателей', 'sum'),
        'PROC.3': ('Коэффициент конверсии обращений', 'mean'),
        'PROC.4': ('Уровень удержания благополучателей', 'mean'),
        'SOC.1': ('Индекс достижения социальной реабилитации', 'mean'),
        'SOC.2': ('Количество благополучателей, прошедших профориентацию', 'sum'),
        'SOC.3': ('Уровень удовлетворенности благополучателей', 'mean'),
        'FIN.1': ('Стоимость оказания услуг на 1 благополучателя', 'mean'),
        'FIN.2': ('Отклонение от сметы', 'mean'),
        'FIN.3': ('Коэффициент привлечения натуральной помощи', 'mean'),
    }
    
    # Группируем по датам
    unique_dates = pd.concat([
        krasnodar_data['Дата_Начала'],
        krymsk_data['Дата_Начала']
    ]).unique()
    
    for date_val in unique_dates:
        kras_date_data = krasnodar_data[krasnodar_data['Дата_Начала'] == date_val]
        krym_date_data = krymsk_data[krymsk_data['Дата_Начала'] == date_val]
        
        # Агрегируем каждый KPI
        for kpi_suffix, (kpi_name, agg_type) in kpi_mappings.items():
            kras_kpi = kras_date_data[kras_date_data['KPI_ID'].str.endswith(kpi_suffix)]
            krym_kpi = krym_date_data[krym_date_data['KPI_ID'].str.endswith(kpi_suffix)]
            
            if not kras_kpi.empty or not krym_kpi.empty:
                # Вычисляем агрегированное значение
                if agg_type == 'sum':
                    fact_val = kras_kpi['Факт'].sum() + krym_kpi['Факт'].sum()
                    min_val = kras_kpi['Минимум'].sum() + krym_kpi['Минимум'].sum()
                    target_val = kras_kpi['Цель'].sum() + krym_kpi['Цель'].sum()
                else:  # mean
                    values = pd.concat([kras_kpi['Факт'], krym_kpi['Факт']])
                    fact_val = values.mean() if not values.empty else 0
                    
                    min_values = pd.concat([kras_kpi['Минимум'], krym_kpi['Минимум']])
                    min_val = min_values.mean() if not min_values.empty else 0
                    
                    target_values = pd.concat([kras_kpi['Цель'], krym_kpi['Цель']])
                    target_val = target_values.mean() if not target_values.empty else 0
                
                # Определяем категорию
                if 'PROC' in kpi_suffix:
                    category = "Верь в себя - Общие (Процессы)"
                elif 'SOC' in kpi_suffix:
                    category = "Верь в себя - Общие (Соц. воздействие)"
                else:
                    category = "Верь в себя - Общие (Финансы)"
                
                # Получаем информацию о неделе и промежутке дат
                if not kras_kpi.empty:
                    week_id = kras_kpi.iloc[0]['Неделя_Год']
                    date_range = kras_kpi.iloc[0]['Промежуток_Дат']
                    date_end = kras_kpi.iloc[0].get('Дата_Окончания', date_val)
                elif not krym_kpi.empty:
                    week_id = krym_kpi.iloc[0]['Неделя_Год']
                    date_range = krym_kpi.iloc[0]['Промежуток_Дат']
                    date_end = krym_kpi.iloc[0].get('Дата_Окончания', date_val)
                else:
                    continue
                
                aggregated_records.append({
                    'Дата_Начала': date_val,
                    'Дата_Окончания': date_end,
                    'Неделя_Год': week_id,
                    'Промежуток_Дат': date_range,
                    'Категория': category,
                    'KPI_ID': f'KPI.ВС.ОБЩИЕ.{kpi_suffix}',
                    'Название': kpi_name,
                    'Минимум': round(min_val, 2),
                    'Цель': round(target_val, 2),
                    'Факт': round(fact_val, 2),
                    'Комментарий': 'Агрегированные данные'
                })
    
    return pd.DataFrame(aggregated_records)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_aggregation_type(kpi_name):
    """Определяет тип агрегации (mean или sum) на основе названия KPI."""
    # Ключевые слова, указывающие на усреднение
    keywords_mean = ["%", "Коэффициент", "Индекс", "Уровень", "Стоимость", "Доля", "CTR", "ER", "DCR", "Share Rate", "Средний", "Скорость", "в работе"]
    if any(k in kpi_name for k in keywords_mean):
        return 'mean'
    return 'sum'


def filter_data_by_period(df, start_date, end_date, granularity):
    """Фильтрует и группирует данные по выбранному диапазону и гранулярности с учетом типа агрегации."""
    df = df.copy()

    # Преобразование в datetime64[ns]
    df['Дата_Начала_DT'] = pd.to_datetime(df['Дата_Начала'], errors='coerce')
    numerical_cols = ['Минимум', 'Цель', 'Факт']

    # Отбрасываем строки без даты
    df = df.dropna(subset=['Дата_Начала_DT'])
    
    # Фильтрация по диапазону дат
    mask = (df['Дата_Начала_DT'].dt.date >= start_date) & (df['Дата_Начала_DT'].dt.date <= end_date)
    df = df.loc[mask]

    if df.empty:
        return pd.DataFrame()

    # Определение правила группировки (Resampling rule)
    freq_map = {
        "День": "D",
        "Неделя": "W-SUN",  # Неделя заканчивается в воскресенье
        "Месяц": "MS",
        "Квартал": "QS",
        "Год": "YS"
    }
    freq = freq_map.get(granularity, "MS")

    # Разделяем KPI на те, что нужно суммировать, и те, что нужно усреднять
    df['Agg_Type'] = df['Название'].apply(get_aggregation_type)
    
    df_mean = df[df['Agg_Type'] == 'mean']
    df_sum = df[df['Agg_Type'] == 'sum']
    
    results = []
    
    # Группировка для средних
    if not df_mean.empty:
        res_mean = df_mean.groupby([pd.Grouper(key='Дата_Начала_DT', freq=freq, label='right'), 'Название'])[numerical_cols].mean().reset_index()
        results.append(res_mean)
        
    # Группировка для сумм
    if not df_sum.empty:
        res_sum = df_sum.groupby([pd.Grouper(key='Дата_Начала_DT', freq=freq, label='right'), 'Название'])[numerical_cols].sum().reset_index()
        results.append(res_sum)
    
    if results:
        df_grouped = pd.concat(results).reset_index(drop=True)
    else:
        return pd.DataFrame()

    # Форматирование периода для отображения
    if granularity == "День":
        df_grouped['Период'] = df_grouped['Дата_Начала_DT'].dt.strftime('%d.%m.%Y')
    elif granularity == "Неделя":
        # Функция для формирования лейбла недели с учетом границ фильтра
        def format_week_label(week_end_dt):
            # week_end_dt - это воскресенье (из-за W-SUN и label='right')
            week_start_dt = week_end_dt - timedelta(days=6)
            
            # Обрезаем по границам выбранного периода
            # start_date и end_date приходят как date objects, конвертируем для сравнения
            filter_start = pd.Timestamp(start_date)
            filter_end = pd.Timestamp(end_date)
            
            actual_start = max(week_start_dt, filter_start)
            actual_end = min(week_end_dt, filter_end)
            
            return f"{actual_start.strftime('%d.%m')} - {actual_end.strftime('%d.%m.%Y')}"

        df_grouped['Период'] = df_grouped['Дата_Начала_DT'].apply(format_week_label)
        
    elif granularity == "Месяц":
        df_grouped['Период'] = df_grouped['Дата_Начала_DT'].dt.strftime('%B %Y')
    elif granularity == "Квартал":
        df_grouped['Период'] = df_grouped['Дата_Начала_DT'].apply(lambda x: f"Q{pd.Timestamp(x).quarter} {x.year}")
    elif granularity == "Год":
        df_grouped['Период'] = df_grouped['Дата_Начала_DT'].dt.strftime('%Y')

    # Сортировка
    df_grouped = df_grouped.sort_values('Дата_Начала_DT')

    return df_grouped[['Название', 'Минимум', 'Цель', 'Факт', 'Период']]


def render_program_financials(program_name, end_date):
    """
    Отображает финансовые показатели программы за месяц
    - Определяет месяц из end_date
    - Показывает доходы, расходы, окупаемость
    - Если данных нет, показывает уведомление и последние доступные данные
    
    Args:
        program_name: название программы (например, "Верь в себя - Краснодар")
        end_date: дата окончания отчетного периода
    """
    if not FINANCIALS_MODULE_AVAILABLE:
        st.warning("⚠️ Модуль финансов недоступен")
        return
    
    # Определяем месяц и год из end_date
    target_year = end_date.year
    target_month = end_date.month
    
    # Получаем данные с fallback
    data = get_financial_data_with_fallback(program_name, target_year, target_month)
    
    # Показываем предупреждение, если данных нет
    if data['warning']:
        st.warning(f"⚠️ {data['warning']}")
    
    # Отображаем метрики
    col1, col2, col3 = st.columns(3)
    
    month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                  "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    
    with col1:
        st.metric(
            f"Доходы ({month_names[data['month']-1]} {data['year']})",
            f"{data['income']:,.0f} ₽"
        )
    
    with col2:
        st.metric(
            "Расходы",
            f"{data['expenses']:,.0f} ₽"
        )
    
    with col3:
        profitability_val = data['profitability']
        st.metric(
            "Окупаемость",
            f"{profitability_val:.1f}%",
            delta="Прибыль" if profitability_val > 0 else ("Убыток" if profitability_val < 0 else None)
        )


def render_chart(df_grouped, kpi_name, title_prefix="Динамика"):
    chart_data = df_grouped[df_grouped['Название'] == kpi_name]

    if chart_data.empty:
        fig = go.Figure()
        fig.update_layout(
            annotations=[dict(text="Нет данных для построения графика", showarrow=False)],
            xaxis={'visible': False}, yaxis={'visible': False}, height=350, title=f"{title_prefix}: {kpi_name}"
        )
        return fig

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=chart_data['Период'], y=chart_data['Цель'], name='Цель', line=dict(color='green', dash='dash')))
    fig.add_trace(go.Scatter(x=chart_data['Период'], y=chart_data['Минимум'], name='Минимум',
                             line=dict(color='orange', dash='dot')))
    fig.add_trace(
        go.Scatter(x=chart_data['Период'], y=chart_data['Факт'], name='Факт', line=dict(color='blue', width=3),
                   mode='lines+markers'))

    fig.update_layout(
        title=f"{title_prefix}: {kpi_name}",
        xaxis_title="Отчетный период",
        yaxis_title="Значение",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    if len(chart_data['Период'].unique()) > 6:
        fig.update_xaxes(tickangle=45)

    return fig


# --- ИНТЕРФЕЙС ---

st.sidebar.title("🕊️ Синяя Птица")

# --- ИНФОРМАЦИЯ ОБ ИСТОЧНИКЕ ДАННЫХ ---
if 'data_source' in st.session_state:
    source_info = {
        "loaded_from_file": ("💾", "Данные загружены из файла"),
        "generated_mock_data": ("🔧", "Тестовые данные (первый запуск)"),
        "corrupted_file_recovered": ("⚠️", "Восстановлено после ошибки")
    }
    icon, message = source_info.get(st.session_state.data_source, ("ℹ️", "Неизвестно"))
    st.sidebar.info(f"{icon} **Источник данных:**\n{message}")

# --- КНОПКА СБРОСА ДАННЫХ (РЕМОНТ) ---
with st.sidebar.expander("⚙️ Управление данными", expanded=False):
    st.markdown("**Внимание:** Эта операция удалит ВСЕ данные!")
    
    if st.button("🚨 Очистить всю базу данных", key="reset_all_data"):
        # Полная очистка - создаем пустую базу
        st.session_state.kpi_history = pd.DataFrame(columns=REQUIRED_COLUMNS)
        save_to_file(st.session_state.kpi_history)
        st.session_state.data_source = "manually_cleared"
        st.success("✅ База данных очищена")
        st.rerun()
    
    st.divider()
    
    if st.button("🔄 Восстановить тестовые данные", key="restore_mock_data"):
        # Генерируем новые тестовые данные
        st.session_state.kpi_history = generate_mock_data()
        save_to_file(st.session_state.kpi_history)
        st.session_state.data_source = "generated_mock_data"
        st.success("✅ Тестовые данные восстановлены")
        st.rerun()

# --- ИНФОРМАЦИЯ О СОХРАНЕНИИ ---
if os.path.exists(BACKUP_FILE):
    file_time = datetime.fromtimestamp(os.path.getmtime(BACKUP_FILE))
    st.sidebar.info(f"💾 Последнее сохранение:\n{file_time.strftime('%d.%m.%Y %H:%M:%S')}")

st.sidebar.markdown(f"**Записей в базе:** {len(st.session_state.kpi_history)}")

# --- БОКОВОЕ МЕНЮ ---
with st.sidebar:
    st.header("Навигация")
    menu = st.selectbox(
        "Выберите раздел:",
        ["Сводный Дашборд", "Динамика Сборов", "SMM Эффективность", "Корпоративный Фандрайзинг", "Мониторинг Кампаний", "Финансы программ", "Ввод данных KPI", "История (Редактор)"]
    )
    
    st.divider()
    st.markdown("### Управление данными")

# --- 1. СВОДНЫЙ ДАШБОРД ---
if menu == "Сводный Дашборд":
    st.title("📊 Сводный операционный дашборд")

    col_per1, col_per2 = st.columns([2, 1])
    with col_per1:
        # Выбор диапазона дат
        today = datetime.now().date()
        start_of_year = date(today.year, 1, 1)
        
        date_range = st.date_input(
            "Период отчета:",
            value=(start_of_year, today),
            key="dashboard_date_range"
        )
    
    with col_per2:
        # Ограничение гранулярности
        if isinstance(date_range, tuple) and len(date_range) == 2:
            duration_days = (date_range[1] - date_range[0]).days
        else:
            duration_days = 0
            
        available_granularities = ["День"]
        if duration_days > 7:
            available_granularities.append("Неделя")
        if duration_days > 30:
            available_granularities.append("Месяц")
        if duration_days > 90:
            available_granularities.append("Квартал")
        if duration_days > 365:
            available_granularities.append("Год")
            
        # Выбор гранулярности
        granularity = st.selectbox(
            "Шаг графика:",
            available_granularities,
            index=len(available_granularities)-1, # Default to largest available
            key="dashboard_granularity"
        )

    # Обработка случая, когда выбрана только одна дата в диапазоне
    if isinstance(date_range, tuple):
        if len(date_range) == 2:
            start_date, end_date = date_range
        elif len(date_range) == 1:
            start_date = end_date = date_range[0]
        else:
            start_date = end_date = today
    else:
        start_date = end_date = date_range

    st.divider()

    df_source = st.session_state.kpi_history.copy()
    df_viz = filter_data_by_period(df_source, start_date, end_date, granularity)

    if df_viz.empty:
        st.warning("Нет данных для отображения за выбранный период. Проверьте вкладку 'История (Редактор)'.")
    else:
        st.subheader("Ключевые показатели")
        
        # Общий финансовый показатель
        kpi_finance = "Выполнение общего плана фандрайзинга, %"
        st.plotly_chart(render_chart(df_viz, kpi_finance), use_container_width=True)

        st.divider()
        st.subheader("Программы")
        
        # Агрегируем данные по центрам перед отображением
        aggregated_data = aggregate_center_kpis(df_source, start_date, end_date)
        
        # Объединяем исходные данные с агрегированными
        if not aggregated_data.empty:
            df_source_with_agg = pd.concat([df_source, aggregated_data], ignore_index=True)
            df_viz_all = filter_data_by_period(df_source_with_agg, start_date, end_date, granularity)
        else:
            df_viz_all = df_viz
        
        prog_tabs = st.tabs(["Верь в себя", "Нужна помощь", "ЯЖивой"])
        
        # --- "Верь в себя" с подвкладками по центрам ---
        with prog_tabs[0]:
            st.markdown("### Центры развития программы \"Верь в себя\"")
            
            center_tabs = st.tabs(["Краснодар", "Крымск", "Общие"])
            
            # Краснодар
            with center_tabs[0]:
                st.markdown("#### Центр развития: Краснодар")
                
                # Финансовые показатели
                render_program_financials("Верь в себя - Краснодар", end_date)
                
                st.divider()
                st.markdown("**KPI показатели:**")
                
                c_vs_kr1, c_vs_kr2 = st.columns(2)
                with c_vs_kr1:
                    st.plotly_chart(render_chart(df_viz_all, "Количество проведенных занятий (факт/план)"), use_container_width=True, key="chart_vs_kr_classes")
                with c_vs_kr2:
                    st.plotly_chart(render_chart(df_viz_all, "Количество обслуженных благополучателей"), use_container_width=True, key="chart_vs_kr_beneficiaries")
                
                st.plotly_chart(render_chart(df_viz_all, "Индекс достижения социальной реабилитации"), use_container_width=True, key="chart_vs_kr_social_rehab")
            
            # Крымск
            with center_tabs[1]:
                st.markdown("#### Центр развития: Крымск")
                
                # Финансовые показатели
                render_program_financials("Верь в себя - Крымск", end_date)
                
                st.divider()
                st.markdown("**KPI показатели:**")
                
                c_vs_krm1, c_vs_krm2 = st.columns(2)
                with c_vs_krm1:
                    st.plotly_chart(render_chart(df_viz_all, "Количество проведенных занятий (факт/план)"), use_container_width=True, key="chart_vs_krm_classes")
                with c_vs_krm2:
                    st.plotly_chart(render_chart(df_viz_all, "Количество обслуженных благополучателей"), use_container_width=True, key="chart_vs_krm_beneficiaries")
                
                st.plotly_chart(render_chart(df_viz_all, "Индекс достижения социальной реабилитации"), use_container_width=True, key="chart_vs_krm_social_rehab")
            
            # Общие (агрегированные)
            with center_tabs[2]:
                st.markdown("#### Общие показатели (Краснодар + Крымск)")
                
                # Финансовые показатели - агрегированные
                if FINANCIALS_MODULE_AVAILABLE:
                    target_year = end_date.year
                    target_month = end_date.month
                    
                    # Получаем агрегированные финансовые данные
                    agg_financials = get_aggregated_financials(target_year, target_month)
                    
                    if 'Верь в себя - Общие' in agg_financials:
                        total_data = agg_financials['Верь в себя - Общие']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                                      "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
                        
                        with col1:
                            st.metric(
                                f"Доходы ({month_names[target_month-1]} {target_year})",
                                f"{total_data['income']:,.0f} ₽"
                            )
                        
                        with col2:
                            st.metric(
                                "Расходы",
                                f"{total_data['expenses']:,.0f} ₽"
                            )
                        
                        with col3:
                            st.metric(
                                "Окупаемость",
                                f"{total_data['profitability']:.1f}%",
                                delta="Прибыль" if total_data['profitability'] > 0 else ("Убыток" if total_data['profitability'] < 0 else None)
                            )
                    else:
                        st.warning("⚠️ Нет финансовых данных по центрам за выбранный период")
                
                st.divider()
                st.markdown("**Агрегированные KPI показатели:**")
                
                c_vs_all1, c_vs_all2 = st.columns(2)
                with c_vs_all1:
                    st.plotly_chart(render_chart(df_viz_all, "Количество проведенных занятий (факт/план)"), use_container_width=True, key="chart_vs_all_classes")
                with c_vs_all2:
                    st.plotly_chart(render_chart(df_viz_all, "Количество обслуженных благополучателей"), use_container_width=True, key="chart_vs_all_beneficiaries")
                
                st.plotly_chart(render_chart(df_viz_all, "Индекс достижения социальной реабилитации"), use_container_width=True, key="chart_vs_all_social_rehab")

        # --- "Нужна помощь" ---
        with prog_tabs[1]:
            st.markdown("### Программа \"Нужна помощь\"")
            
            # Финансовые показатели
            render_program_financials("Нужна помощь", end_date)
            
            st.divider()
            st.markdown("**KPI показатели:**")
            
            c_np1, c_np2 = st.columns(2)
            with c_np1:
                st.plotly_chart(render_chart(df_viz, "Количество обслуженных благополучателей"), use_container_width=True, key="chart_np_beneficiaries")
            with c_np2:
                st.plotly_chart(render_chart(df_viz, "Объем предоставленной помощи (денежная форма)"), use_container_width=True, key="chart_np_money")
            
            st.plotly_chart(render_chart(df_viz, "Коэффициент своевременности рассмотрения заявок"), use_container_width=True, key="chart_np_timeliness")

        # --- "ЯЖивой" ---
        with prog_tabs[2]:
            st.markdown("### Программа \"ЯЖивой\"")
            
            # Финансовые показатели
            render_program_financials("ЯЖивой", end_date)
            
            st.divider()
            st.markdown("**KPI показатели:**")
            
            c_yz1, c_yz2 = st.columns(2)
            with c_yz1:
                st.plotly_chart(render_chart(df_viz, "Количество обслуженных благополучателей"), use_container_width=True, key="chart_yz_beneficiaries")
            with c_yz2:
                st.plotly_chart(render_chart(df_viz, "Объем предоставленной целевой помощи"), use_container_width=True, key="chart_yz_target_aid")
            
            st.plotly_chart(render_chart(df_viz, "Индекс достижения социальной адаптации"), use_container_width=True, key="chart_yz_social_adapt")

# --- 1.1 ДИНАМИКА СБОРОВ (НОВЫЙ РАЗДЕЛ) ---
elif menu == "Динамика Сборов":
    st.title("📈 Динамика Сборов и Эффективность")
    
    # Константа стоимости часа (можно вынести в настройки)
    DEFAULT_HOURLY_RATE = 500.0

    col_fr1, col_fr2 = st.columns([2, 1])
    with col_fr1:
        # Выбор диапазона дат
        today = datetime.now().date()
        start_of_year = date(today.year, 1, 1)
        
        fr_date_range = st.date_input(
            "Период отчета:",
            value=(start_of_year, today),
            key="fr_date_range"
        )
    
    with col_fr2:
        # Ограничение гранулярности
        if isinstance(fr_date_range, tuple) and len(fr_date_range) == 2:
            fr_duration_days = (fr_date_range[1] - fr_date_range[0]).days
        else:
            fr_duration_days = 0
            
        fr_available_granularities = ["День"]
        if fr_duration_days > 7:
            fr_available_granularities.append("Неделя")
        if fr_duration_days > 30:
            fr_available_granularities.append("Месяц")
        if fr_duration_days > 90:
            fr_available_granularities.append("Квартал")
        if fr_duration_days > 365:
            fr_available_granularities.append("Год")

        # Выбор гранулярности
        fr_granularity = st.selectbox(
            "Шаг графика:",
            fr_available_granularities,
            index=len(fr_available_granularities)-1, 
            key="fr_granularity"
        )

    # Обработка диапазона
    if isinstance(fr_date_range, tuple):
        if len(fr_date_range) == 2:
            fr_start, fr_end = fr_date_range
        elif len(fr_date_range) == 1:
            fr_start = fr_end = fr_date_range[0]
        else:
            fr_start = fr_end = today
    else:
        fr_start = fr_end = fr_date_range

    st.divider()

    df_source = st.session_state.kpi_history.copy()
    df_fr_viz = filter_data_by_period(df_source, fr_start, fr_end, fr_granularity)

    if df_fr_viz.empty:
        st.warning("Нет данных для отображения за выбранный период.")
    else:
        # --- РАСЧЕТ МЕТРИК ---
        # Нам нужно сгруппировать данные по периодам, чтобы посчитать производные метрики (ROI, CoF)
        # filter_data_by_period уже возвращает сгруппированные данные по 'Название' и 'Период'
        
        # Разворачиваем таблицу (pivot), чтобы метрики стали колонками
        df_pivot = df_fr_viz.pivot(index='Период', columns='Название', values='Факт').reset_index()
        
        # Заполняем пропуски нулями для корректного расчета
        df_pivot = df_pivot.fillna(0)
        
        # Определяем названия колонок (ключи могут отличаться, используем точные названия из KPI_STRUCTURE)
        col_costs = "Прямые расходы (Реклама/Бюджет), руб."
        col_hours = "Трудозатраты персонала, ч."
        col_funds = "Привлеченные средства (Факт), руб."
        col_donors = "Количество доноров, чел."
        col_reach = "Охват (Просмотры), ед."
        col_actions = "Целевые действия (Конверсии), ед."
        
        # Проверяем наличие колонок
        available_cols = df_pivot.columns.tolist()
        
        # Расчет производных метрик
        if col_costs in available_cols and col_hours in available_cols and col_funds in available_cols:
            df_pivot['Total_Cost'] = df_pivot[col_costs] + (df_pivot[col_hours] * DEFAULT_HOURLY_RATE)
            
            # ROI = (Income - Cost) / Cost * 100
            df_pivot['ROI'] = df_pivot.apply(
                lambda row: ((row[col_funds] - row['Total_Cost']) / row['Total_Cost'] * 100) if row['Total_Cost'] > 0 else 0, axis=1
            )
            
            # CoF = Cost / Income
            df_pivot['CoF'] = df_pivot.apply(
                lambda row: (row['Total_Cost'] / row[col_funds]) if row[col_funds] > 0 else 0, axis=1
            )
        else:
            df_pivot['ROI'] = 0
            df_pivot['CoF'] = 0
            
        if col_reach in available_cols and col_actions in available_cols:
             df_pivot['Conversion'] = df_pivot.apply(
                lambda row: (row[col_actions] / row[col_reach] * 100) if row[col_reach] > 0 else 0, axis=1
            )
        else:
            df_pivot['Conversion'] = 0

        # --- ОТОБРАЖЕНИЕ КАРТОЧЕК (СРЕДНИЕ ЗА ПЕРИОД) ---
        avg_roi = df_pivot['ROI'].mean()
        avg_cof = df_pivot['CoF'].mean()
        avg_conv = df_pivot['Conversion'].mean()
        
        st.subheader("Сводные показатели эффективности")
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.metric("Средний ROI", f"{avg_roi:.1f}%", delta=f"{avg_roi - 100:.1f}%" if avg_roi > 0 else None)
            st.caption("Цель: > 200%")
            
        with m2:
            st.metric("Стоимость сбора (CoF)", f"{avg_cof:.2f} ₽", delta=None)
            st.caption("Затраты на 1 привлеченный рубль")
            
        with m3:
            st.metric("Конверсия (CR)", f"{avg_conv:.2f}%", delta=None)
            st.caption("Из охвата в действие")

        st.divider()
        
        # --- ГРАФИКИ ---
        
        # 1. ROI и CoF
        st.subheader("Финансовая эффективность")
        
        fig_roi = go.Figure()
        fig_roi.add_trace(go.Scatter(x=df_pivot['Период'], y=df_pivot['ROI'], name='ROI (%)', line=dict(color='green', width=3)))
        fig_roi.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Убыточность")
        fig_roi.update_layout(title="Динамика ROI (Возврат инвестиций)", yaxis_title="ROI, %", height=350)
        st.plotly_chart(fig_roi, use_container_width=True)
        
        fig_cof = go.Figure()
        fig_cof.add_trace(go.Bar(x=df_pivot['Период'], y=df_pivot['CoF'], name='CoF (Cost of Fundraising)', marker_color='orange'))
        fig_cof.update_layout(title="Динамика стоимости сбора (CoF)", yaxis_title="Затраты на 1 руб.", height=350)
        st.plotly_chart(fig_cof, use_container_width=True)
        
        # 2. Воронка / Конверсия
        st.subheader("Операционная продуктивность")
        
        c_conv1, c_conv2 = st.columns(2)
        with c_conv1:
            # График конверсии
            fig_conv = go.Figure()
            fig_conv.add_trace(go.Scatter(x=df_pivot['Период'], y=df_pivot['Conversion'], name='Конверсия %', line=dict(color='purple', width=3), fill='tozeroy'))
            fig_conv.update_layout(title="Динамика Конверсии", yaxis_title="%", height=350)
            st.plotly_chart(fig_conv, use_container_width=True)
            
        with c_conv2:
            # Абсолютные значения (Охват vs Действия)
            if col_reach in available_cols and col_actions in available_cols:
                fig_funnel = go.Figure()
                fig_funnel.add_trace(go.Bar(x=df_pivot['Период'], y=df_pivot[col_reach], name='Охват', marker_color='lightblue'))
                fig_funnel.add_trace(go.Scatter(x=df_pivot['Период'], y=df_pivot[col_actions], name='Действия', yaxis='y2', line=dict(color='blue', width=3)))
                
                fig_funnel.update_layout(
                    title="Воронка: Охват vs Действия",
                    yaxis=dict(title="Охват"),
                    yaxis2=dict(title="Действия", overlaying='y', side='right'),
                    height=350,
                    legend=dict(x=0, y=1.1, orientation='h')
                )
                st.plotly_chart(fig_funnel, use_container_width=True)

# --- 2. SMM ЭФФЕКТИВНОСТЬ ---
elif menu == "SMM Эффективность":
    st.title("📱 SMM Эффективность")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        # Выбор диапазона дат
        today = datetime.now().date()
        start_of_year = date(today.year, 1, 1)
        
        smm_date_range = st.date_input(
            "Период отчета:",
            value=(start_of_year, today),
            key="smm_date_range"
        )
    
    with col_s2:
        # Ограничение гранулярности
        if isinstance(smm_date_range, tuple) and len(smm_date_range) == 2:
            s_duration_days = (smm_date_range[1] - smm_date_range[0]).days
        else:
            s_duration_days = 0
            
        s_available_granularities = ["День"]
        if s_duration_days > 7:
            s_available_granularities.append("Неделя")
        if s_duration_days > 30:
            s_available_granularities.append("Месяц")
        if s_duration_days > 90:
            s_available_granularities.append("Квартал")
        if s_duration_days > 365:
            s_available_granularities.append("Год")

        # Выбор гранулярности
        smm_granularity = st.selectbox(
            "Шаг графика:",
            s_available_granularities,
            index=len(s_available_granularities)-1, # Default to largest available
            key="smm_granularity"
        )

    # Обработка диапазона
    if isinstance(smm_date_range, tuple):
        if len(smm_date_range) == 2:
            s_start, s_end = smm_date_range
        elif len(smm_date_range) == 1:
            s_start = s_end = smm_date_range[0]
        else:
            s_start = s_end = today
    else:
        s_start = s_end = smm_date_range

    st.divider()

    df_source = st.session_state.kpi_history.copy()
    df_smm_viz = filter_data_by_period(df_source, s_start, s_end, smm_granularity)

    if df_smm_viz.empty:
        st.warning("Нет данных для отображения за выбранный период.")
    else:
        # 3.1 Вовлеченность
        st.subheader("3.1 Вовлеченность (Engagement)")
        tabs = st.tabs(["ER (Engagement Rate)", "Share Rate", "CTR"])

        with tabs[0]:
            st.plotly_chart(render_chart(df_smm_viz, "ER (Engagement Rate), % [KPI.СММ.1]"), use_container_width=True, key="smm_er")

        with tabs[1]:
            st.plotly_chart(render_chart(df_smm_viz, "Share Rate (Репосты), %"), use_container_width=True, key="smm_share")

        with tabs[2]:
            st.plotly_chart(render_chart(df_smm_viz, "CTR (Клики на сайт), %"), use_container_width=True, key="smm_ctr")

        # 3.2 Фандрайзинг
        st.subheader("3.2 SMM Фандрайзинг")
        c_fund1, c_fund2 = st.columns(2)
        with c_fund1:
            st.plotly_chart(render_chart(df_smm_viz, "DCR (Конверсия в донат), %"), use_container_width=True, key="smm_dcr")
        with c_fund2:
            st.plotly_chart(render_chart(df_smm_viz, "Сумма сбора SMM, руб. (Часть KPI.ФР.1)"), use_container_width=True, key="smm_money")


# --- 2.1 КОРПОРАТИВНЫЙ ФАНДРАЙЗИНГ ---
elif menu == "Корпоративный Фандрайзинг":
    st.title("🤝 Корпоративный Фандрайзинг")

    col_cf1, col_cf2 = st.columns([2, 1])
    with col_cf1:
        # Выбор диапазона дат
        today = datetime.now().date()
        start_of_year = date(today.year, 1, 1)
        
        cf_date_range = st.date_input(
            "Период отчета:",
            value=(start_of_year, today),
            key="cf_date_range"
        )
    
    with col_cf2:
        # Ограничение гранулярности
        if isinstance(cf_date_range, tuple) and len(cf_date_range) == 2:
            cf_duration_days = (cf_date_range[1] - cf_date_range[0]).days
        else:
            cf_duration_days = 0
            
        cf_available_granularities = ["День"]
        if cf_duration_days > 7:
            cf_available_granularities.append("Неделя")
        if cf_duration_days > 30:
            cf_available_granularities.append("Месяц")
        if cf_duration_days > 90:
            cf_available_granularities.append("Квартал")
        if cf_duration_days > 365:
            cf_available_granularities.append("Год")

        # Выбор гранулярности
        cf_granularity = st.selectbox(
            "Шаг графика:",
            cf_available_granularities,
            index=len(cf_available_granularities)-1, # Default to largest available
            key="cf_granularity"
        )

    # Обработка диапазона
    if isinstance(cf_date_range, tuple):
        if len(cf_date_range) == 2:
            cf_start, cf_end = cf_date_range
        elif len(cf_date_range) == 1:
            cf_start = cf_end = cf_date_range[0]
        else:
            cf_start = cf_end = today
    else:
        cf_start = cf_end = cf_date_range

    st.divider()

    df_source = st.session_state.kpi_history.copy()
    df_cf_viz = filter_data_by_period(df_source, cf_start, cf_end, cf_granularity)

    if df_cf_viz.empty:
        st.warning("Нет данных для отображения за выбранный период.")
    else:
        # Вкладки: Результат и Деятельность
        cf_tabs = st.tabs(["Результат", "Деятельность"])

        with cf_tabs[0]:
            st.subheader("Финансовые и партнерские результаты")
            
            c_res1, c_res2 = st.columns(2)
            with c_res1:
                st.plotly_chart(render_chart(df_cf_viz, "Объем привлеченных средств, руб."), use_container_width=True, key="cf_res_money")
                st.plotly_chart(render_chart(df_cf_viz, "Средний чек сделки, руб."), use_container_width=True, key="cf_res_avg_check")
            with c_res2:
                st.plotly_chart(render_chart(df_cf_viz, "Количество новых партнеров"), use_container_width=True, key="cf_res_new_partners")
                st.plotly_chart(render_chart(df_cf_viz, "Стоимость привлечения партнера, руб."), use_container_width=True, key="cf_res_cac")
            
            st.plotly_chart(render_chart(df_cf_viz, "Коэффициент удержания партнеров, %"), use_container_width=True, key="cf_res_retention")

        with cf_tabs[1]:
            st.subheader("Воронка продаж и активность")
            
            c_act1, c_act2 = st.columns(2)
            with c_act1:
                st.plotly_chart(render_chart(df_cf_viz, "Количество установленных первых контактов"), use_container_width=True, key="cf_act_contacts")
                st.plotly_chart(render_chart(df_cf_viz, "Количество личных встреч с ЛПР"), use_container_width=True, key="cf_act_meetings")
            with c_act2:
                st.plotly_chart(render_chart(df_cf_viz, "Количество отправленных предложений"), use_container_width=True, key="cf_act_offers")
                st.plotly_chart(render_chart(df_cf_viz, "Количество партнеров в работе"), use_container_width=True, key="cf_act_pipeline")
            
            st.plotly_chart(render_chart(df_cf_viz, "Скорость конверсии (дни)"), use_container_width=True, key="cf_act_conversion_speed")


# --- 2.2 МОНИТОРИНГ КАМПАНИЙ ---
elif menu == "Мониторинг Кампаний":
    st.title("🎯 Мониторинг Фандрайзинговых Кампаний")
    
    if not CAMPAIGNS_MODULE_AVAILABLE:
        st.error(f"❌ Модули мониторинга кампаний недоступны. Ошибка: {CAMPAIGNS_ERROR}")
        st.info("Попробуйте перезапустить приложение или проверить установку зависимостей (plotly).")
    else:
        # Инициализация данных кампаний в session_state
        if 'campaigns_data' not in st.session_state:
            st.session_state.campaigns_data = load_campaigns()
        
        # Вкладки
        campaign_tabs = st.tabs(["📊 Сводка", "🔍 Детали", "➕ Новая кампания", "💰 Обновление сборов", "🌐 Мультиканальность", "📈 Сравнение каналов", "✏️ Редактор"])
        
        # --- Вкладка 1: Сводка ---
        with campaign_tabs[0]:
            st.subheader("Общая сводка всех кампаний")
            
            campaigns_df = load_campaigns()
            
            if not campaigns_df.empty:
                # Фильтры
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    filter_status = st.multiselect(
                        "Фильтр по статусу",
                        options=["active", "completed", "paused"],
                        default=["active"],
                        format_func=lambda x: {"active": "🟢 Активна", "completed": "✅ Завершена", "paused": "⏸️ Приостановлена"}[x]
                    )
                
                with filter_col2:
                    filter_channel = st.multiselect(
                        "Фильтр по каналу",
                        options=campaigns_df['channel'].unique().tolist(),
                        default=campaigns_df['channel'].unique().tolist()
                    )
                
                # Применяем фильтры
                filtered_df = campaigns_df[
                    (campaigns_df['status'].isin(filter_status)) &
                    (campaigns_df['channel'].isin(filter_channel))
                ]
                
                st.divider()
                
                # Сводная таблица
                render_campaign_summary_table(filtered_df)
                
                # Общая статистика
                st.divider()
                st.subheader("📈 Общая статистика")
                
                stat1, stat2, stat3, stat4 = st.columns(4)
                
                with stat1:
                    total_campaigns = len(filtered_df)
                    st.metric("Всего кампаний", total_campaigns)
                
                with stat2:
                    total_collected = filtered_df['collected_amount'].sum()
                    st.metric("Всего собрано", f"{total_collected:,.0f} ₽")
                
                with stat3:
                    total_target = filtered_df['target_amount'].sum()
                    st.metric("Общая цель", f"{total_target:,.0f} ₽")
                
                with stat4:
                    overall_progress = (total_collected / total_target * 100) if total_target > 0 else 0
                    st.metric("Общий прогресс", f"{overall_progress:.1f}%")
            else:
                st.info("📭 Нет кампаний. Создайте первую кампанию на вкладке 'Новая кампания'.")
        
        # --- Вкладка 2: Детали ---
        with campaign_tabs[1]:
            st.subheader("Детальная аналитика кампании")
            
            campaigns_df = load_campaigns()
            
            if not campaigns_df.empty:
                # Выбор кампании
                campaign_options = {
                    row['campaign_id']: f"{row['name']} ({row['channel']})"
                    for _, row in campaigns_df.iterrows()
                }
                
                selected_id = st.selectbox(
                    "Выберите кампанию для детального просмотра:",
                    options=list(campaign_options.keys()),
                    format_func=lambda x: campaign_options[x]
                )
                
                if selected_id:
                    st.divider()
                    render_campaign_detail_view(selected_id)
                    
                    # Экспорт отчета
                    st.divider()
                    st.subheader("📥 Экспорт отчета")
                    
                    export_col1, export_col2 = st.columns([2, 1])
                    
                    with export_col1:
                        st.markdown("Скачайте детальный отчет по кампании для ЕОС или архива.")
                    
                    with export_col2:
                        export_format = st.radio("Формат:", ["CSV", "Excel"], horizontal=True)
                        
                        if st.button("⬇️ Скачать отчет", key="download_campaign_report"):
                            report_data = export_campaign_report(
                                selected_id,
                                format='csv' if export_format == 'CSV' else 'excel'
                            )
                            
                            if report_data:
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                filename = f"campaign_report_{selected_id}_{timestamp}.{'csv' if export_format == 'CSV' else 'xlsx'}"
                                mime_type = 'text/csv' if export_format == 'CSV' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                
                                st.download_button(
                                    label=f"💾 {filename}",
                                    data=report_data,
                                    file_name=filename,
                                    mime=mime_type
                                )
            else:
                st.info("📭 Нет кампаний для просмотра.")
        
        # --- Вкладка 3: Новая кампания ---
        with campaign_tabs[2]:
            render_campaign_input_form()
        
        # --- Вкладка 4: Обновление сборов ---
        with campaign_tabs[3]:
            render_collection_update_form()
            
        # --- Вкладка 5: Мультиканальность ---
        with campaign_tabs[4]:
            render_multi_channel_dashboard()
        
        # --- Вкладка 6: Сравнение каналов ---
        with campaign_tabs[5]:
            st.subheader("📊 Сравнительный анализ каналов")
            
            campaigns_df = load_campaigns()
            
            if not campaigns_df.empty:
                # График сравнения
                st.plotly_chart(render_channel_comparison(campaigns_df), use_container_width=True)
                
                st.divider()
                
                # Детальная таблица
                st.subheader("Детализация по каналам")
                
                channels_data = compare_channels(campaigns_df)
                
                if not channels_data.empty:
                    # Форматирование для отображения
                    display_df = channels_data.copy()
                    display_df['total_collected'] = display_df['total_collected'].apply(lambda x: f"{x:,.0f} ₽")
                    display_df['total_costs'] = display_df['total_costs'].apply(lambda x: f"{x:,.0f} ₽")
                    display_df['avg_roi'] = display_df['avg_roi'].apply(lambda x: f"{x:.1f}%")
                    display_df['avg_cof'] = display_df['avg_cof'].apply(lambda x: f"{x:.2f}")
                    display_df['avg_ctr'] = display_df['avg_ctr'].apply(lambda x: f"{x:.2f}%")
                    display_df['avg_dcr'] = display_df['avg_dcr'].apply(lambda x: f"{x:.2f}%")
                    display_df['avg_donation'] = display_df['avg_donation'].apply(lambda x: f"{x:,.0f} ₽")
                    
                    display_df.columns = [
                        'Канал', 'Кампаний', 'Собрано', 'Затраты',
                        'ROI', 'CoF', 'CTR', 'DCR', 'Доноров', 'Ср. донат'
                    ]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Рекомендации
                    st.divider()
                    st.subheader("💡 Рекомендации по каналам")
                    
                    best_roi_channel = channels_data.loc[channels_data['avg_roi'].idxmax(), 'channel']
                    best_ctr_channel = channels_data.loc[channels_data['avg_ctr'].idxmax(), 'channel']
                    best_dcr_channel = channels_data.loc[channels_data['avg_dcr'].idxmax(), 'channel']
                    
                    st.success(f"✅ **Лучший ROI:** {best_roi_channel}")
                    st.info(f"🎯 **Лучший CTR:** {best_ctr_channel}")
                    st.info(f"💎 **Лучший DCR:** {best_dcr_channel}")
            else:
                st.info("📭 Нет данных для сравнения. Создайте хотя бы одну кампанию.")
        
        # --- Вкладка 7: Редактор ---
        with campaign_tabs[6]:
            render_campaign_editor()


# --- ФИНАНСЫ ПРОГРАММ ---
elif menu == "Финансы программ":
    st.title("💰 Финансы программ")
    
    if not FINANCIALS_MODULE_AVAILABLE:
        st.error(f"⚠️ Модуль финансов недоступен: {FINANCIALS_ERROR}")
    else:
        st.markdown("""
        Ввод месячных финансовых данных по программам.
        **Данные вводятся помесячно** и используются для расчета окупаемости программ.
        """)
        
        tab1, tab2 = st.tabs(["📝 Ввод данных", "📊 История"])
        
        # --- Вкладка 1: Ввод данных ---
        with tab1:
            st.subheader("Ввод финансовых данных")
            
            with st.form("financial_data_form", clear_on_submit=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    program = st.selectbox(
                        "Программа *",
                        PROGRAMS,
                        help="Выберите программу для ввода данных"
                    )
                
                with col2:
                    current_year = datetime.now().year
                    current_month = datetime.now().month
                    
                    col_month, col_year = st.columns(2)
                    
                    with col_month:
                        month = st.selectbox(
                            "Месяц *",
                            range(1, 13),
                            index=current_month - 1,
                            format_func=lambda x: [
                                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
                            ][x-1]
                        )
                    
                    with col_year:
                        year = st.number_input(
                            "Год *",
                            min_value=2020,
                            max_value=2030,
                            value=current_year,
                            step=1
                        )
                
                st.divider()
                
                col_income, col_expenses = st.columns(2)
                
                with col_income:
                    income = st.number_input(
                        "Доходы (руб.) *",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        format="%.2f",
                        help="Общие доходы программы за месяц"
                    )
                
                with col_expenses:
                    expenses = st.number_input(
                        "Расходы (руб.) *",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        format="%.2f",
                        help="Общие расходы программы за месяц"
                    )
                
                # Расчет окупаемости
                if expenses > 0:
                    profitability = calculate_profitability(income, expenses)
                    
                    st.info(f"📊 **Расчетная окупаемость:** {profitability:.2f}%")
                    
                    if profitability < 0:
                        st.warning("⚠️ Программа убыточна (расходы превышают доходы)")
                    elif profitability < 20:
                        st.warning("⚠️ Низкая окупаемость")
                    else:
                        st.success("✅ Хорошая окупаемость")
                
                note = st.text_area(
                    "Примечание",
                    placeholder="Дополнительная информация о финансовых показателях...",
                    height=100
                )
                
                submitted = st.form_submit_button("💾 Сохранить данные", use_container_width=True)
                
                if submitted:
                    if income == 0 and expenses == 0:
                        st.error("❌ Введите хотя бы одно значение (доходы или расходы)")
                    else:
                        result = add_financial_record(
                            program=program,
                            year=int(year),
                            month=int(month),
                            income=income,
                            expenses=expenses,
                            note=note
                        )
                        
                        if result['success']:
                            if result.get('updated'):
                                st.success(f"✅ {result['message']}")
                                st.info(f"Новая окупаемость: {result['profitability']:.2f}%")
                            else:
                                st.success(f"✅ {result['message']}")
                                st.success(f"Окупаемость: {result['profitability']:.2f}%")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['message']}")
        
        # --- Вкладка 2: История ---
        with tab2:
            st.subheader("История финансовых данных")
            
            # Фильтр по программе
            filter_program = st.selectbox(
                "Фильтр по программе:",
                ["Все программы"] + PROGRAMS,
                key="history_filter"
            )
            
            # Загружаем историю
            if filter_program == "Все программы":
                all_data = load_financials()
                if not all_data.empty:
                    # Добавляем вычисляемое поле окупаемости
                    all_data['profitability'] = all_data.apply(
                        lambda row: calculate_profitability(row['income'], row['expenses']), 
                        axis=1
                    )
                    all_data = all_data.sort_values(['year', 'month'], ascending=False)
                history_df = all_data
            else:
                history_df = get_program_history(filter_program)
            
            if history_df.empty:
                st.info("📭 Нет данных для отображения")
            else:
                # Форматируем для отображения
                display_df = history_df.copy()
                
                # Добавляем название месяца
                month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                              "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
                
                display_df['Месяц'] = display_df['month'].apply(lambda x: month_names[int(x)-1] if 1 <= x <= 12 else str(x))
                display_df['Год'] = display_df['year'].astype(int)
                display_df['Программа'] = display_df['program']
                display_df['Доходы'] = display_df['income'].apply(lambda x: f"{x:,.0f} ₽")
                display_df['Расходы'] = display_df['expenses'].apply(lambda x: f"{x:,.0f} ₽")
                display_df['Окупаемость'] = display_df['profitability'].apply(lambda x: f"{x:.2f}%")
                display_df['Примечание'] = display_df['note'].fillna('')
                
                # Выбираем колонки для отображения
                display_columns = ['Программа', 'Год', 'Месяц', 'Доходы', 'Расходы', 'Окупаемость', 'Примечание']
                
                st.dataframe(
                    display_df[display_columns],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Статистика
                st.divider()
                st.subheader("📈 Статистика")
                
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                
                with stat_col1:
                    total_income = display_df['income'].sum()
                    st.metric("Общие доходы", f"{total_income:,.0f} ₽")
                
                with stat_col2:
                    total_expenses = display_df['expenses'].sum()
                    st.metric("Общие расходы", f"{total_expenses:,.0f} ₽")
                
                with stat_col3:
                    total_profit = total_income - total_expenses
                    st.metric("Прибыль/Убыток", f"{total_profit:,.0f} ₽")
                
                with stat_col4:
                    avg_profitability = display_df['profitability'].mean()
                    st.metric("Средняя окупаемость", f"{avg_profitability:.2f}%")


# --- 3. ВВОД ДАННЫХ KPI ---
elif menu == "Ввод данных KPI":
    st.title("📝 Ввод новых показателей")
    st.markdown("Выберите категорию и показатель. Все поля обязательны. Данные вносятся за неделю.")

    col_date, col_cat = st.columns(2)

    with col_date:
        input_date_range = st.date_input(
            "1. Выберите период (начало и конец)",
            value=(datetime.now().date(), datetime.now().date() + timedelta(days=6)),
            key="input_date_range"
        )

    with col_cat:
        category = st.selectbox(
            "2. Категория",
            list(KPI_STRUCTURE.keys()),
            key="input_category_key"
        )

    # Обработка диапазона
    if isinstance(input_date_range, tuple):
        if len(input_date_range) == 2:
            start_date, end_date = input_date_range
        elif len(input_date_range) == 1:
            start_date = end_date = input_date_range[0]
        else:
            start_date = end_date = datetime.now().date()
    else:
        start_date = end_date = input_date_range

    # Расчет недели и отображение (справочно)
    _, week_id, _ = get_week_info(start_date)
    date_range_str = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
    
    st.info(f"Выбранный период: **{date_range_str}** (нач. неделя {week_id})")

    available_kpis = KPI_STRUCTURE.get(category, {})

    if available_kpis:
        kpi_display = {k: v for k, v in available_kpis.items()}

        selected_kpi_key = st.selectbox(
            "3. Показатель",
            list(kpi_display.keys()),
            format_func=lambda x: kpi_display[x],
            key="input_kpi_key"
        )
        kpi_name_full = kpi_display[selected_kpi_key]
    else:
        st.warning("Нет показателей для данной категории.")
        selected_kpi_key = None
        kpi_name_full = ""

    st.divider()

    # Сбор остальных данных
    if selected_kpi_key:
        c_min, c_target, c_fact = st.columns(3)
        with c_min:
            val_min = st.number_input("Минимум (Красная зона)", value=0.0, step=0.01, key="input_min")
        with c_target:
            val_target = st.number_input("Цель (План)", value=0.0, step=0.01, key="input_target")
        with c_fact:
            val_fact = st.number_input("Факт", value=0.0, step=0.01, key="input_fact")

        comment = st.text_area("Комментарий / Причина отклонения", key="input_comment")

        submitted = st.button("💾 Сохранить в базу")

        if submitted:
            new_row = {
                "Дата_Начала": start_date,
                "Дата_Окончания": end_date,
                "Неделя_Год": week_id,
                "Промежуток_Дат": date_range_str,
                "Категория": category,
                "KPI_ID": selected_kpi_key,
                "Название": kpi_name_full,
                "Минимум": val_min,
                "Цель": val_target,
                "Факт": val_fact,
                "Комментарий": comment
            }

            # Добавляем новую строку
            new_df = pd.DataFrame([new_row])
            st.session_state.kpi_history = pd.concat(
                [st.session_state.kpi_history, new_df],
                ignore_index=True
            )

            # Сохраняем в файл
            save_to_file(st.session_state.kpi_history)

            st.success(f"✅ Показатель '{kpi_name_full}' за {date_range_str} успешно добавлен!")
            st.rerun()
    else:
        st.warning("Выберите действительный KPI, чтобы ввести данные.")


# --- 4. ИСТОРИЯ (РЕДАКТОР) ---
elif menu == "История (Редактор)":
    st.title("🗄️ Управление данными (CRUD)")
    st.info("""
    **Инструкция:**
    * Для **редактирования**: кликните дважды по ячейке, измените значение и нажмите Enter.
    * Для **удаления**: выделите строки (галочкой слева) и нажмите клавишу `Delete`.
    * Изменения сохраняются автоматически.
    """)

    if st.session_state.kpi_history.empty:
        st.warning("База данных пуста.")

    else:

        # Подготовка данных для редактора (сортировка)
        df_display = st.session_state.kpi_history.sort_values("Дата_Начала", ascending=False)

        # Конфигурация колонок
        column_config = {
            "KPI_ID": st.column_config.TextColumn("KPI ID", disabled=True),
            "Дата_Начала": st.column_config.DateColumn("Дата начала", format="DD.MM.YYYY"),
            "Дата_Окончания": st.column_config.DateColumn("Дата окончания", format="DD.MM.YYYY"),
            "Неделя_Год": st.column_config.TextColumn("Неделя (ГГГГ-WW)", disabled=True),
            "Промежуток_Дат": st.column_config.TextColumn("Отчетный период", disabled=True),

            "Категория": st.column_config.SelectboxColumn("Категория", options=list(KPI_STRUCTURE.keys()),
                                                          required=True),
            "Название": st.column_config.TextColumn("KPI"),
            "Минимум": st.column_config.NumberColumn("Мин", format="%.2f", step=0.01),
            "Цель": st.column_config.NumberColumn("План", format="%.2f", step=0.01),
            "Факт": st.column_config.NumberColumn("Факт", format="%.2f", step=0.01),
            "Комментарий": st.column_config.TextColumn("Комментарий", width="large")
        }

        edited_df = st.data_editor(
            df_display,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="editor"
        )

        # Логика сохранения изменений
        # Сравниваем edited_df с исходным df_display, чтобы понять, были ли изменения
        if not edited_df.equals(df_display):
            
            # Применяем очистку типов
            cleaned = clean_data_types(edited_df)
            
            # Проверка на потерю данных
            if cleaned.empty and not edited_df.empty:
                st.error("Ошибка сохранения: данные повреждены при обработке.")
            else:
                # Обновляем session_state
                st.session_state.kpi_history = cleaned
                
                # Сохраняем в файл
                save_to_file(st.session_state.kpi_history)
                
                st.success("✅ Изменения сохранены.")
                st.rerun()
        
        # --- СТАТИСТИКА ---
        st.divider()
        st.subheader("📊 Статистика базы данных")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Всего записей", len(st.session_state.kpi_history))
        
        with stat_col2:
            unique_kpis = st.session_state.kpi_history['Название'].nunique()
            st.metric("Уникальных KPI", unique_kpis)
        
        with stat_col3:
            unique_categories = st.session_state.kpi_history['Категория'].nunique()
            st.metric("Категорий", unique_categories)
        
        with stat_col4:
            if 'Дата_Начала' in st.session_state.kpi_history.columns:
                date_range_days = (
                    pd.to_datetime(st.session_state.kpi_history['Дата_Начала']).max() - 
                    pd.to_datetime(st.session_state.kpi_history['Дата_Начала']).min()
                ).days
                st.metric("Диапазон дней", date_range_days)
        
        # Распределение по категориям
        st.markdown("**Распределение записей по категориям:**")
        category_counts = st.session_state.kpi_history['Категория'].value_counts()
        
        for cat, count in category_counts.items():
            st.caption(f"• {cat}: {count} записей")
        
        # --- ЭКСПОРТ ДАННЫХ ---
        st.divider()
        st.subheader("📥 Экспорт данных")
        
        col_export1, col_export2 = st.columns([2, 1])
        
        with col_export1:
            st.markdown("Скачайте все данные в формате CSV для анализа в Excel или Google Sheets.")
        
        with col_export2:
            # Подготовка CSV
            csv_data = st.session_state.kpi_history.to_csv(index=False, encoding='utf-8-sig')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"kpi_data_{timestamp}.csv"
            
            st.download_button(
                label="⬇️ Скачать CSV",
                data=csv_data,
                file_name=filename,
                mime='text/csv',
                key='download_csv_button'
            )