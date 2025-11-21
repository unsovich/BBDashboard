import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# --- НАСТРОЙКИ И КОНСТАНТЫ ---
st.set_page_config(page_title="АНО «Синяя птица» - KPI Monitor", layout="wide")

# Словарь всех KPI по категориям
KPI_STRUCTURE = {
    "SMM (Вовлеченность)": {
        "SMM.ER": "Engagement Rate (ER), %",
        "SMM.SHARE": "Share Rate (Репосты), %",
        "SMM.CTR": "CTR (Клики на сайт), %"
    },
    "SMM (Фандрайзинг)": {
        "SMM.DCR": "DCR (Конверсия в донат), %",
        "SMM.MONEY": "Сумма сбора SMM, руб."
    },
    "Программы": {
        "PROG.FILL": "Заполняемость центров (Верь в себя), %",
        "PROG.TIME": "Своевременность помощи (Нужна помощь), %",
        "PROG.MONITOR": "Мониторинг использования (ЯЖивой), %"
    },
    "Финансы и Админ": {
        "FIN.PLAN": "Выполнение плана фандрайзинга (Общий), %",
        "FIN.BUDGET": "Соблюдение бюджета (Расходы), %",
        "HR.VOL": "Прирост волонтеров, %"
    }
}


# --- ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ (ИСТОРИЯ) ---
# Чтобы дашборд не был пустым при первом запуске
def generate_mock_data():
    data = []
    # Генерируем данные с января по текущий момент
    start_date = datetime(2024, 1, 1)
    categories = ["SMM.ER", "SMM.MONEY", "FIN.PLAN", "PROG.FILL"]

    for i in range(180):  # 180 дней истории
        current_date = start_date + timedelta(days=i)

        # Пример: SMM Сборы (случайные колебания)
        data.append({
            "Дата": current_date,
            "Категория": "SMM (Фандрайзинг)",
            "KPI_ID": "SMM.MONEY",
            "Название": "Сумма сбора SMM, руб.",
            "Минимум": 45000,
            "Цель": 60000,
            "Факт": np.random.randint(40000, 75000),
            "Комментарий": ""
        })

        # Пример: ER (раз в неделю)
        if current_date.weekday() == 0:  # Раз в неделю
            data.append({
                "Дата": current_date,
                "Категория": "SMM (Вовлеченность)",
                "KPI_ID": "SMM.ER",
                "Название": "Engagement Rate (ER), %",
                "Минимум": 2.5,
                "Цель": 4.0,
                "Факт": np.random.uniform(2.0, 5.5),
                "Комментарий": "Успешный рилс" if np.random.random() > 0.8 else ""
            })

    return pd.DataFrame(data)


# Инициализация Session State
if 'kpi_history' not in st.session_state:
    st.session_state.kpi_history = generate_mock_data()

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.title("🕊️ Синяя Птица")
menu = st.sidebar.radio("Меню", ["Сводный Дашборд", "SMM Аналитика", "Ввод данных KPI", "База данных"])


# --- ФУНКЦИЯ ОТРИСОВКИ ГРАФИКА ---
def plot_kpi_dynamics(df, kpi_name, period_mode):
    # Фильтрация и группировка
    chart_data = df[df['Название'] == kpi_name].copy()
    chart_data['Дата'] = pd.to_datetime(chart_data['Дата'])

    if period_mode == "Год (по месяцам)":
        chart_data['Период'] = chart_data['Дата'].dt.strftime('%Y-%m')
    else:
        chart_data['Период'] = chart_data['Дата'].dt.strftime('%Y-%m-%d')

    # Агрегация (среднее для процентов, сумма для денег - упрощенно берем среднее для графика динамики выполнения)
    # Для корректности лучше брать сумму для абсолютных величин, но для универсальности здесь use mean
    grouped = chart_data.groupby('Период')[['Минимум', 'Цель', 'Факт']].mean().reset_index()

    fig = go.Figure()

    # Линия Цели
    fig.add_trace(
        go.Scatter(x=grouped['Период'], y=grouped['Цель'], name='Цель', line=dict(color='green', dash='dash')))
    # Линия Минимума
    fig.add_trace(
        go.Scatter(x=grouped['Период'], y=grouped['Минимум'], name='Минимум', line=dict(color='orange', dash='dot')))
    # Линия Факта
    fig.add_trace(go.Scatter(x=grouped['Период'], y=grouped['Факт'], name='Факт', line=dict(color='blue', width=3),
                             mode='lines+markers'))

    fig.update_layout(title=f"Динамика: {kpi_name}", xaxis_title="Период", yaxis_title="Значение", height=350)
    return fig


# --- 1. СВОДНЫЙ ОПЕРАЦИОННЫЙ ДАШБОРД ---
if menu == "Сводный Дашборд":
    st.title("📊 Сводный операционный дашборд")

    # Фильтры времени
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        period_mode = st.selectbox("Детализация периода", ["Год (по месяцам)", "Месяц (по дням/неделям)"])

    st.divider()

    # Основные показатели (Top Level)
    df = st.session_state.kpi_history

    # Отображаем графики для ключевых метрик разных отделов
    st.subheader("Ключевые показатели эффективности (Top Level)")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_kpi_dynamics(df, "Сумма сбора SMM, руб.", period_mode), use_container_width=True)
    with col2:
        st.plotly_chart(plot_kpi_dynamics(df, "Engagement Rate (ER), %", period_mode), use_container_width=True)

    # Таблица отклонений (где Факт < Минимума) за последний месяц
    st.subheader("⚠️ Зона внимания (Отклонения за последние 30 дней)")
    last_month = df[df['Дата'] > (datetime.now() - timedelta(days=30))]
    alerts = last_month[last_month['Факт'] < last_month['Минимум']].copy()

    if not alerts.empty:
        st.dataframe(
            alerts[['Дата', 'Название', 'Цель', 'Факт', 'Комментарий']].style.format(
                {'Цель': '{:.1f}', 'Факт': '{:.1f}'}),
            use_container_width=True
        )
    else:
        st.success("За последние 30 дней критических отклонений не зафиксировано.")

# --- 2. SMM АНАЛИТИКА (Выделенный раздел) ---
elif menu == "SMM Аналитика":
    st.title("📱 SMM Эффективность")
    st.markdown("Мониторинг вовлеченности и конверсии в пожертвования.")

    df = st.session_state.kpi_history

    # Метрики "В карточках" (среднее за последний месяц)
    last_30 = df[(df['Дата'] > (datetime.now() - timedelta(days=30))) & (df['Категория'].str.contains("SMM"))]

    if not last_30.empty:
        cols = st.columns(4)
        metrics = [
            ("SMM.ER", "Engagement Rate"),
            ("SMM.SHARE", "Share Rate"),
            ("SMM.CTR", "CTR (Клики)"),
            ("SMM.DCR", "Conv. to Donate")
        ]

        for i, (kpi_id, label) in enumerate(metrics):
            metric_data = last_30[last_30['KPI_ID'] == kpi_id]
            if not metric_data.empty:
                avg_val = metric_data['Факт'].mean()
                target_val = metric_data['Цель'].mean()
                delta = avg_val - target_val
                cols[i].metric(label, f"{avg_val:.2f}%", f"{delta:.2f}%")
            else:
                cols[i].metric(label, "-", "-")

    st.divider()

    # Графики вовлеченности
    st.subheader("1. Воронка Вовлеченности")
    tab_er, tab_sh, tab_ctr = st.tabs(["ER (Вовлеченность)", "Share Rate", "CTR"])

    with tab_er:
        st.plotly_chart(plot_kpi_dynamics(df, "Engagement Rate (ER), %", "Год (по месяцам)"), use_container_width=True)
    with tab_sh:
        st.plotly_chart(plot_kpi_dynamics(df, "Share Rate (Репосты), %", "Год (по месяцам)"), use_container_width=True)

    # Графики Фандрайзинга
    st.subheader("2. SMM Фандрайзинг")
    st.plotly_chart(plot_kpi_dynamics(df, "Сумма сбора SMM, руб.", "Год (по месяцам)"), use_container_width=True)

# --- 3. ВВОД ДАННЫХ (ПЛАН / ФАКТ) ---
elif menu == "Ввод данных KPI":
    st.title("📝 Ввод данных KPI")
    st.info("Внесение плановых и фактических показателей за отчетный период.")

    with st.form("kpi_input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            input_date = st.date_input("Отчетная дата", datetime.now())
            category = st.selectbox("Категория", list(KPI_STRUCTURE.keys()))

        with c2:
            # Динамическое обновление списка KPI на основе категории
            kpi_options = KPI_STRUCTURE[category]
            selected_kpi_key = st.selectbox("Показатель", list(kpi_options.keys()),
                                            format_func=lambda x: kpi_options[x])
            kpi_name_full = kpi_options[selected_kpi_key]

        st.subheader("Значения")
        col_val1, col_val2, col_val3 = st.columns(3)
        with col_val1:
            val_min = st.number_input("Минимум (Красная зона)", value=0.0)
        with col_val2:
            val_target = st.number_input("Цель (План)", value=0.0)
        with col_val3:
            val_fact = st.number_input("Факт", value=0.0)

        comment = st.text_area("Комментарий (причины отклонений, корректирующие действия)")

        submitted = st.form_submit_button("Сохранить показатель")

        if submitted:
            new_record = {
                "Дата": pd.to_datetime(input_date),
                "Категория": category,
                "KPI_ID": selected_kpi_key,
                "Название": kpi_name_full,
                "Минимум": val_min,
                "Цель": val_target,
                "Факт": val_fact,
                "Комментарий": comment
            }
            # Добавляем в историю (через concat для DataFrame)
            new_df = pd.DataFrame([new_record])
            st.session_state.kpi_history = pd.concat([st.session_state.kpi_history, new_df], ignore_index=True)
            st.success(f"Данные по {kpi_name_full} сохранены!")

# --- 4. БАЗА ДАННЫХ ---
elif menu == "База данных":
    st.title("🗄️ История показателей")

    df = st.session_state.kpi_history

    # Фильтры таблицы
    kpi_filter = st.multiselect("Фильтр по KPI", df['Название'].unique())
    if kpi_filter:
        df = df[df['Название'].isin(kpi_filter)]

    st.dataframe(
        df.sort_values(by="Дата", ascending=False),
        use_container_width=True,
        column_config={
            "Дата": st.column_config.DateColumn("Дата", format="DD.MM.YYYY"),
            "Минимум": st.column_config.NumberColumn("Мин", format="%.2f"),
            "Цель": st.column_config.NumberColumn("План", format="%.2f"),
            "Факт": st.column_config.NumberColumn("Факт", format="%.2f"),
        }
    )


    # Кнопка скачивания
    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')


    csv = convert_df(df)
    st.download_button(
        label="📥 Скачать CSV",
        data=csv,
        file_name='kpi_history.csv',
        mime='text/csv',
    )