import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np
import pickle
import os

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
if 'kpi_history' not in st.session_state:
    # Пытаемся загрузить из файла
    loaded_data = load_from_file()
    if loaded_data is not None and not loaded_data.empty:
        st.session_state.kpi_history = loaded_data
    else:
        st.session_state.kpi_history = generate_mock_data()
        save_to_file(st.session_state.kpi_history)
    st.session_state.data_initialized = True


# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Убрана автоматическая очистка при каждом обновлении страницы
# Данные НЕ очищаются при каждом рендере


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def filter_data_by_period(df, period_type, selected_month_str=None):
    """Фильтрует и группирует данные: по месяцам (для Года) или по неделям (для Месяца)."""
    df = df.copy()

    # Преобразование в datetime64[ns] для Pandas-агрегации
    df['Дата_Начала_DT'] = pd.to_datetime(df['Дата_Начала'], errors='coerce')
    numerical_cols = ['Минимум', 'Цель', 'Факт']

    # Отбрасываем строки, где нет даты или названия
    df = df.dropna(subset=['Дата_Начала_DT', 'Название'])
    if df.empty:
        return pd.DataFrame()

    # Фильтрация и группировка
    if period_type == "Год (по месяцам)":
        # Ключ для группировки и сортировки (YYYY-MM)
        df['Period_Key'] = df['Дата_Начала_DT'].dt.strftime('%Y-%m')

        # Метка для оси X (Январь 2024)
        df['Период_Display'] = df['Дата_Начала_DT'].dt.strftime('%B %Y')

        # Группируем по ключу периода и Названию KPI
        df_grouped = df.groupby(['Period_Key', 'Период_Display', 'Название'])[numerical_cols].mean().reset_index()

        # Сортируем по надежному строковому ключу
        df_grouped = df_grouped.sort_values('Period_Key')
        df_grouped['Период'] = df_grouped['Период_Display']

    else:  # Месяц (по неделям)
        if selected_month_str is None:
            return pd.DataFrame()

        y, m = map(int, selected_month_str.split('-'))

        # Фильтрация по году и месяцу
        df_filtered = df[(df['Дата_Начала_DT'].dt.year == y) & (df['Дата_Начала_DT'].dt.month == m)].copy()

        if df_filtered.empty:
            return pd.DataFrame()

        # Группировка по уже существующим надежным строковым колонкам
        df_grouped = df_filtered.groupby(['Неделя_Год', 'Промежуток_Дат', 'Название'])[
            numerical_cols].mean().reset_index()
        df_grouped = df_grouped.sort_values('Неделя_Год')
        df_grouped['Период'] = df_grouped['Промежуток_Дат']

    # Возвращаем только необходимые для графика колонки
    return df_grouped[['Название', 'Минимум', 'Цель', 'Факт', 'Период']]


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

# --- КНОПКА СБРОСА ДАННЫХ (РЕМОНТ) ---
if st.sidebar.button("🚨 СБРОСИТЬ ВСЕ ДАННЫЕ (РЕМОНТ)"):
    # Clear corrupted data and regenerate mock data
    st.session_state.kpi_history = generate_mock_data()
    save_to_file(st.session_state.kpi_history)
    st.rerun()

# --- ИНФОРМАЦИЯ О СОХРАНЕНИИ ---
if os.path.exists(BACKUP_FILE):
    file_time = datetime.fromtimestamp(os.path.getmtime(BACKUP_FILE))
    st.sidebar.info(f"💾 Последнее сохранение:\n{file_time.strftime('%d.%m.%Y %H:%M:%S')}")

st.sidebar.markdown(f"**Записей в базе:** {len(st.session_state.kpi_history)}")

# --- МЕНЮ ---
menu = st.sidebar.radio("Навигация", ["Сводный Дашборд", "SMM Эффективность", "Ввод данных KPI", "История (Редактор)"])

# --- 1. СВОДНЫЙ ДАШБОРД ---
if menu == "Сводный Дашборд":
    st.title("📊 Сводный операционный дашборд")

    col_per1, col_per2 = st.columns([1, 2])
    with col_per1:
        period_type = st.radio("Период отчета:", ["Год (по месяцам)", "Месяц (по неделям)"], horizontal=True,
                               key="dashboard_period_radio")

    selected_month_str = None
    if period_type == "Месяц (по неделям)":
        with col_per2:
            df_dates = st.session_state.kpi_history.copy()
            df_dates['Дата_Начала_DT'] = pd.to_datetime(df_dates['Дата_Начала'], errors='coerce')
            df_dates = df_dates.dropna(subset=['Дата_Начала_DT'])
            df_dates['Month_Str'] = df_dates['Дата_Начала_DT'].dt.strftime('%Y-%m')
            available_months = sorted(df_dates['Month_Str'].unique(), reverse=True)

            if not available_months:
                available_months = [datetime.now().strftime('%Y-%m')]

            default_index = 0 if available_months else 0
            selected_month_str = st.selectbox("Выберите месяц:", available_months, index=default_index,
                                              key="dashboard_month_select")

    st.divider()

    df_source = st.session_state.kpi_history.copy()
    df_viz = filter_data_by_period(df_source, period_type, selected_month_str)

    if df_viz.empty:
        st.warning("Нет данных для отображения за выбранный период. Проверьте вкладку 'История (Редактор)'.")
    else:
        st.subheader("Ключевые показатели (Финансы и Программы)")
        c1, c2 = st.columns(2)

        kpi_finance = "Выполнение общего плана фандрайзинга, %"
        kpi_program = "Заполняемость центров (Верь в себя), %"

        with c1:
            st.plotly_chart(render_chart(df_viz, kpi_finance), use_container_width=True)
        with c2:
            st.plotly_chart(render_chart(df_viz, kpi_program), use_container_width=True)

# --- 2. SMM ЭФФЕКТИВНОСТЬ ---
elif menu == "SMM Эффективность":
    st.title("📱 SMM Эффективность")

    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        smm_period_type = st.radio("Масштаб:", ["Год (по месяцам)", "Месяц (по неделям)"], horizontal=True,
                                   key="smm_radio")

    smm_month_str = None
    if smm_period_type == "Месяц (по неделям)":
        with col_s2:
            df_dates = st.session_state.kpi_history.copy()
            df_dates['Дата_Начала_DT'] = pd.to_datetime(df_dates['Дата_Начала'], errors='coerce')
            df_dates = df_dates.dropna(subset=['Дата_Начала_DT'])
            df_dates['Month_Str'] = df_dates['Дата_Начала_DT'].dt.strftime('%Y-%m')
            smm_months = sorted(df_dates['Month_Str'].unique(), reverse=True)
            default_index = 0 if smm_months else 0
            smm_month_str = st.selectbox("Месяц:", smm_months, index=default_index, key="smm_select")

    st.divider()

    df_source = st.session_state.kpi_history.copy()
    df_smm_viz = filter_data_by_period(df_source, smm_period_type, smm_month_str)

    # 3.1 Вовлеченность
    st.subheader("3.1 Вовлеченность (Engagement)")
    tabs = st.tabs(["ER (Engagement Rate)", "Share Rate", "CTR"])

    with tabs[0]:
        st.plotly_chart(render_chart(df_smm_viz, "ER (Engagement Rate), % [KPI.СММ.1]"), use_container_width=True)

    with tabs[1]:
        st.plotly_chart(render_chart(df_smm_viz, "Share Rate (Репосты), %"), use_container_width=True)

    with tabs[2]:
        st.plotly_chart(render_chart(df_smm_viz, "CTR (Клики на сайт), %"), use_container_width=True)

    # 3.2 Фандрайзинг
    st.subheader("3.2 SMM Фандрайзинг")
    c_fund1, c_fund2 = st.columns(2)
    with c_fund1:
        st.plotly_chart(render_chart(df_smm_viz, "DCR (Конверсия в донат), %"), use_container_width=True)
    with c_fund2:
        st.plotly_chart(render_chart(df_smm_viz, "Сумма сбора SMM, руб. (Часть KPI.ФР.1)"), use_container_width=True)


# --- 3. ВВОД ДАННЫХ KPI ---
elif menu == "Ввод данных KPI":
    st.title("📝 Ввод новых показателей")
    st.markdown("Выберите категорию и показатель. Все поля обязательны. Данные вносятся за неделю.")

    col_date, col_cat = st.columns(2)

    with col_date:
        input_date = st.date_input("1. Выберите любую дату в отчетной неделе", datetime.now().date(), key="input_date")

    with col_cat:
        category = st.selectbox(
            "2. Категория",
            list(KPI_STRUCTURE.keys()),
            key="input_category_key"
        )

    # Расчет недели и отображение
    start_of_week, week_id, date_range = get_week_info(input_date)
    st.info(f"Отчетный период: **{date_range}** ({week_id})")

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
                "Дата_Начала": start_of_week,
                "Неделя_Год": week_id,
                "Промежуток_Дат": date_range,
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

            st.success(f"✅ Показатель '{kpi_name_full}' за {date_range} успешно добавлен!")
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

        def save_changes():
            """Безопасное сохранение изменений из редактора"""
            changes = st.session_state.get("editor", None)

            if not isinstance(changes, pd.DataFrame):
                st.warning("Обновление не сохранено: неожиданный формат данных от редактора.")
                return

            # Применяем очистку типов к изменённым данным
            cleaned = clean_data_types(changes)

            # Проверяем, что критические данные не потерялись
            if cleaned.empty and not changes.empty:
                st.error("Ошибка сохранения: данные стали пустыми после обработки. Откатываем изменения.")
                return

            # Проверяем, что основные столбцы присутствуют
            required_for_save = ['KPI_ID', 'Название', 'Дата_Начала']
            if not all(col in cleaned.columns for col in required_for_save):
                st.error("Ошибка: отсутствуют обязательные столбцы. Сохранение отменено.")
                return

            # Только если всё в порядке — сохраняем
            st.session_state.kpi_history = cleaned

            # Сохраняем в файл
            save_to_file(st.session_state.kpi_history)

            st.success("✅ Изменения успешно сохранены.")


        # Конфигурация колонок
        column_config = {
            "KPI_ID": st.column_config.TextColumn("KPI ID", disabled=True),
            "Дата_Начала": st.column_config.DateColumn("Дата начала", format="DD.MM.YYYY", disabled=True),
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

        st.data_editor(
            st.session_state.kpi_history.sort_values("Дата_Начала", ascending=False),
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="editor",
            on_change=save_changes
        )

        csv = st.session_state.kpi_history.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Скачать бэкап (CSV)", csv, "kpi_full_backup.csv", "text/csv")