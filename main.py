import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np

# --- НАСТРОЙКИ И КОНСТАНТЫ ---
st.set_page_config(page_title="АНО «Синяя птица» - KPI Monitor v2.2", layout="wide")

# Полная структура KPI на основе документа [Разделы I и II]
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


# --- ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ ---
def generate_mock_data():
    data = []
    end_date = datetime.now()
    start_date = datetime(end_date.year, 1, 1)
    days_range = (end_date - start_date).days

    # Расширенный список для мок-данных, чтобы все графики работали сразу
    categories_map = {
        "SMM.MONEY": ("SMM (Фандрайзинг)", "Сумма сбора SMM, руб. (Часть KPI.ФР.1)", 40000, 60000),
        "SMM.ER": ("SMM (Вовлеченность)", "ER (Engagement Rate), % [KPI.СММ.1]", 2.5, 4.0),
        "SMM.DCR": ("SMM (Фандрайзинг)", "DCR (Конверсия в донат), %", 1.0, 2.0),
        "SMM.SHARE": ("SMM (Вовлеченность)", "Share Rate (Репосты), %", 0.5, 1.0),
        "KPI.ВС.1": ("Программы", "Заполняемость центров (Верь в себя), %", 85, 95),
        "KPI.ФИН.1": ("Финансы", "Соблюдение бюджета (отклонение), %", 5, 0),
        "KPI.ФР.1_ОБЩИЙ": ("Финансы", "Выполнение общего плана фандрайзинга, %", 80, 100),
    }

    for i in range(days_range + 1):
        current_date = start_date + timedelta(days=i)

        for kpi_id, (cat, name, min_val, target_val) in categories_map.items():
            if np.random.random() > 0.7:

                if kpi_id == "KPI.ФИН.1":
                    fact_val = abs(np.random.normal(2, 2))
                elif 'MONEY' in kpi_id:
                    fact_val = np.random.randint(min_val * 0.8, target_val * 1.2)
                else:
                    fact_val = np.random.normal(target_val, target_val * 0.15)

                fact_val = max(0, fact_val)

                data.append({
                    "Дата": current_date.date(),
                    "Категория": cat,
                    "KPI_ID": kpi_id,
                    "Название": name,
                    "Минимум": min_val,
                    "Цель": target_val,
                    "Факт": round(fact_val, 2),
                    "Комментарий": ""
                })

    return pd.DataFrame(data)


# Инициализация Session State
if 'kpi_history' not in st.session_state:
    st.session_state.kpi_history = generate_mock_data()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (без изменений) ---
def filter_data_by_period(df, period_type, selected_month_str=None):
    df = df.copy()
    df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
    numerical_cols = ['Минимум', 'Цель', 'Факт']
    for col in numerical_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Дата'] + numerical_cols)
    if df.empty:
        return pd.DataFrame()

    if period_type == "Год (по месяцам)":
        df_grouped = df.groupby([df['Дата'].dt.to_period('M'), 'Название'])[numerical_cols].mean().reset_index()
        df_grouped['Период'] = df_grouped['Дата'].dt.strftime('%B %Y')
        df_grouped = df_grouped.sort_values('Дата')
    else:
        y, m = map(int, selected_month_str.split('-'))
        df_filtered = df[(df['Дата'].dt.year == y) & (df['Дата'].dt.month == m)].copy()
        df_grouped = df_filtered.groupby([df_filtered['Дата'], 'Название'])[numerical_cols].mean().reset_index()
        df_grouped['Период'] = df_grouped['Дата'].dt.strftime('%d.%m')
        df_grouped = df_grouped.sort_values('Дата')

    return df_grouped


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
        xaxis_title="Период",
        yaxis_title="Значение",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    return fig


# --- ИНТЕРФЕЙС ---

st.sidebar.title("🕊️ Синяя Птица")
menu = st.sidebar.radio("Навигация", ["Сводный Дашборд", "SMM Эффективность", "Ввод данных KPI", "История (Редактор)"])

# --- 1. СВОДНЫЙ ДАШБОРД (без изменений) ---
if menu == "Сводный Дашборд":
    st.title("📊 Сводный операционный дашборд")

    col_per1, col_per2 = st.columns([1, 2])
    with col_per1:
        period_type = st.radio("Период отчета:", ["Год (по месяцам)", "Месяц (по дням)"], horizontal=True,
                               key="dashboard_period_radio")

    selected_month_str = None
    if period_type == "Месяц (по дням)":
        with col_per2:
            df_dates = st.session_state.kpi_history.copy()
            df_dates['Дата'] = pd.to_datetime(df_dates['Дата'])
            df_dates['Month_Str'] = df_dates['Дата'].dt.to_period('M').astype(str)
            available_months = sorted(df_dates['Month_Str'].unique(), reverse=True)

            if not available_months:
                available_months = [datetime.now().strftime('%Y-%m')]

            selected_month_str = st.selectbox("Выберите месяц:", available_months, key="dashboard_month_select")

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

# --- 2. SMM ЭФФЕКТИВНОСТЬ (без изменений) ---
elif menu == "SMM Эффективность":
    st.title("📱 SMM Эффективность")

    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        smm_period_type = st.radio("Масштаб:", ["Год (по месяцам)", "Месяц (по дням)"], horizontal=True,
                                   key="smm_radio")

    smm_month_str = None
    if smm_period_type == "Месяц (по дням)":
        with col_s2:
            df_dates = st.session_state.kpi_history.copy()
            df_dates['Дата'] = pd.to_datetime(df_dates['Дата'])
            df_dates['Month_Str'] = df_dates['Дата'].dt.to_period('M').astype(str)
            smm_months = sorted(df_dates['Month_Str'].unique(), reverse=True)
            smm_month_str = st.selectbox("Месяц:", smm_months, key="smm_select")

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
    st.markdown("Выберите категорию, затем показатель. Все поля обязательны.")

    # --- ИСПРАВЛЕННАЯ ЛОГИКА: Без st.form и callback, relying on natural rerun ---
    col_cat, col_kpi = st.columns(2)

    with col_cat:
        # Выбор категории. При изменении Streamlit перерисовывает страницу
        category = st.selectbox(
            "1. Категория",
            list(KPI_STRUCTURE.keys()),
            key="input_category_key"  # Ключ для сохранения выбора
        )

    # Получаем доступные KPI, используя текущий выбранный элемент (который Streamlit сохранил по ключу)
    available_kpis = KPI_STRUCTURE.get(category, {})

    with col_kpi:
        if available_kpis:
            kpi_display = {k: v for k, v in available_kpis.items()}
            # Второй selectbox, который зависит от первого
            selected_kpi_key = st.selectbox(
                "2. Показатель",
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
        c_date, c_min, c_target, c_fact = st.columns(4)
        with c_date:
            input_date = st.date_input("Дата отчета", datetime.now(), key="input_date")
        with c_min:
            val_min = st.number_input("Минимум (Красная зона)", value=0.0, step=0.01, key="input_min")
        with c_target:
            val_target = st.number_input("Цель (План)", value=0.0, step=0.01, key="input_target")
        with c_fact:
            val_fact = st.number_input("Факт", value=0.0, step=0.01, key="input_fact")

        comment = st.text_area("Комментарий / Причина отклонения", key="input_comment")

        # Финальная кнопка сохранения
        submitted = st.button("💾 Сохранить в базу")

        if submitted:
            new_row = {
                "Дата": input_date,
                "Категория": category,
                "KPI_ID": selected_kpi_key,
                "Название": kpi_name_full,
                "Минимум": val_min,
                "Цель": val_target,
                "Факт": val_fact,
                "Комментарий": comment
            }
            # Добавление в session_state
            st.session_state.kpi_history = pd.concat(
                [st.session_state.kpi_history, pd.DataFrame([new_row])],
                ignore_index=True
            )
            st.success(f"Показатель '{kpi_name_full}' успешно добавлен!")
            # Принудительная очистка полей формы после успешной отправки (опционально)
            # st.experimental_rerun()
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

    if not st.session_state.kpi_history.empty:

        def save_changes():
            changes = st.session_state["editor"]
            # Приведение даты к правильному формату
            changes['Дата'] = pd.to_datetime(changes['Дата'], errors='coerce').dt.date
            st.session_state.kpi_history = changes


        column_config = {
            "Дата": st.column_config.DateColumn("Дата", format="DD.MM.YYYY", required=True),
            "Категория": st.column_config.SelectboxColumn("Категория", options=list(KPI_STRUCTURE.keys()),
                                                          required=True),
            "Минимум": st.column_config.NumberColumn("Мин", format="%.2f", step=0.01),
            "Цель": st.column_config.NumberColumn("План", format="%.2f", step=0.01),
            "Факт": st.column_config.NumberColumn("Факт", format="%.2f", step=0.01),
            "Комментарий": st.column_config.TextColumn("Комментарий", width="large")
        }

        st.data_editor(
            st.session_state.kpi_history.sort_values("Дата", ascending=False),
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="editor",
            on_change=save_changes
        )

    else:
        st.warning("База данных пуста.")

    csv = st.session_state.kpi_history.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Скачать бэкап (CSV)", csv, "kpi_full_backup.csv", "text/csv")