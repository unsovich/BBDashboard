"""
Модуль UI компонентов для работы с кампаниями
Формы ввода, редакторы, детальные просмотры, экспорт
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
import io

from .campaign_data import (
    add_campaign,
    update_campaign,
    get_campaign_by_id,
    load_campaigns,
    get_campaign_groups,
    add_collection_update,
    get_collection_history,
    get_collection_summary
)
from .campaign_analytics import (
    calculate_campaign_metrics,
    get_campaign_status,
    detect_red_flags,
    generate_recommendations
)
from .campaign_viz import (
    render_progress_chart,
    render_weekly_dynamics,
    render_funnel_chart,
    render_economic_analysis
)


# --- КОНСТАНТЫ ---
CHANNELS = ["VK", "Telegram", "Email", "Website", "YouTube", "Instagram", "Партнёры", "Другое"]
STATUSES = ["active", "completed", "paused"]
STATUS_LABELS = {
    "active": "🟢 Активна",
    "completed": "✅ Завершена",
    "paused": "⏸️ Приостановлена"
}


def render_campaign_input_form() -> None:
    """
    Форма для создания новой кампании
    """
    st.subheader("➕ Создание новой кампании")
    
    with st.form("new_campaign_form", clear_on_submit=True):
        # Основная информация
        st.markdown("### Основная информация")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Название кампании *",
                placeholder="Например: Новогодний сбор 2025",
                help="Укажите понятное название для идентификации кампании"
            )
            
            channel = st.selectbox(
                "Канал *",
                CHANNELS,
                help="Основной канал привлечения доноров"
            )
            
            # Группа кампаний
            existing_groups = get_campaign_groups()
            
            options = ["Без группы", f"Существующая ({len(existing_groups)})", "Новая"]
            group_mode = st.radio("Группа", options, horizontal=True, label_visibility="collapsed")
            
            group_id = None
            if "Существующая" in group_mode:
                if existing_groups:
                    group_id = st.selectbox("Выберите группу", existing_groups)
                    st.success(f"✅ Выбрана группа: **{group_id}**")
                else:
                    st.warning("Нет созданных групп. Выберите 'Новая' для создания.")
            elif group_mode == "Новая":
                group_id = st.text_input("Название новой группы", placeholder="Например: Новый год 2025")
            
            if "Без группы" in group_mode:
                group_id = None
        
        with col2:
            # Даты
            today = datetime.now().date()
            start_date = st.date_input(
                "Дата старта *",
                value=today,
                help="Когда начинается кампания"
            )
            
            end_date = st.date_input(
                "Дата окончания *",
                value=today + timedelta(days=30),
                help="Планируемая дата завершения"
            )
        
        description = st.text_area(
            "Описание кампании",
            placeholder="Краткое описание целей и особенностей кампании",
            height=100
        )
        
        st.divider()
        
        # Финансовые показатели
        st.markdown("### 💰 Финансовые показатели")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            target_amount = st.number_input(
                "Цель сбора (₽) *",
                min_value=0.0,
                value=100000.0,
                step=1000.0,
                help="Целевая сумма сбора"
            )
        
        with col4:
            collected_amount = st.number_input(
                "Уже собрано (₽)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="Если кампания уже началась"
            )
        
        with col5:
            ad_costs = st.number_input(
                "Затраты на рекламу (₽)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="Бюджет на рекламу и продвижение"
            )
        
        st.divider()
        
        # Трудозатраты
        st.markdown("### 👥 Трудозатраты")
        
        col6, col7 = st.columns(2)
        
        with col6:
            labor_hours = st.number_input(
                "Часы работы персонала",
                min_value=0.0,
                value=0.0,
                step=1.0,
                help="Общее время работы команды над кампанией"
            )
        
        with col7:
            hourly_rate = st.number_input(
                "Стоимость часа (₽)",
                min_value=0.0,
                value=500.0,
                step=50.0,
                help="Средняя стоимость часа работы"
            )
        
        st.divider()
        
        # Метрики эффективности
        st.markdown("### 📊 Метрики активности")
        
        col8, col9, col10, col11 = st.columns(4)
        
        with col8:
            reach = st.number_input(
                "Охват (просмотры)",
                min_value=0,
                value=0,
                step=100,
                help="Количество просмотров"
            )
        
        with col9:
            clicks = st.number_input(
                "Клики",
                min_value=0,
                value=0,
                step=10,
                help="Количество переходов"
            )
        
        with col10:
            conversions = st.number_input(
                "Конверсии",
                min_value=0,
                value=0,
                step=1,
                help="Целевые действия"
            )
        
        with col11:
            donors_count = st.number_input(
                "Доноры",
                min_value=0,
                value=0,
                step=1,
                help="Количество донатов"
            )
        
        # Кнопка создания
        submitted = st.form_submit_button("🚀 Создать кампанию", type="primary")
        
        if submitted:
            # Валидация
            if not name:
                st.error("⚠️ Укажите название кампании")
                return
            
            if end_date < start_date:
                st.error("⚠️ Дата окончания не может быть раньше даты старта")
                return
            
            if target_amount <= 0:
                st.error("⚠️ Цель сбора должна быть больше нуля")
                return
            
            # Создание кампании
            result = add_campaign(
                name=name,
                channel=channel,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                target_amount=target_amount,
                collected_amount=collected_amount,
                ad_costs=ad_costs,
                labor_hours=labor_hours,
                hourly_rate=hourly_rate,
                reach=reach,
                clicks=clicks,
                conversions=conversions,
                donors_count=donors_count,
                description=description,
                status="active"
            )
            
            if result['success']:
                st.success(f"✅ {result['message']}")
                st.info(f"ID кампании: `{result['campaign_id']}`")
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")


def render_campaign_editor() -> None:
    """
    Редактор существующих кампаний
    """
    st.subheader("✏️ Редактор кампаний")
    
    campaigns_df = load_campaigns()
    
    if campaigns_df.empty:
        st.info("📭 Нет кампаний для редактирования")
        return
    
    # Конфигурация колонок
    column_config = {
        'campaign_id': st.column_config.TextColumn('ID', disabled=True, width='small'),
        'group_id': st.column_config.TextColumn('Группа', width='medium'),
        'name': st.column_config.TextColumn('Название', width='medium'),
        'channel': st.column_config.SelectboxColumn('Канал', options=CHANNELS, width='small'),
        'start_date': st.column_config.DateColumn('Старт', format='DD.MM.YYYY'),
        'end_date': st.column_config.DateColumn('Окончание', format='DD.MM.YYYY'),
        'status': st.column_config.SelectboxColumn('Статус', options=STATUSES, width='small'),
        'target_amount': st.column_config.NumberColumn('Цель (₽)', format='%.0f'),
        'collected_amount': st.column_config.NumberColumn('Собрано (₽)', format='%.0f'),
        'ad_costs': st.column_config.NumberColumn('Реклама (₽)', format='%.0f'),
        'labor_hours': st.column_config.NumberColumn('Часы', format='%.1f'),
        'hourly_rate': st.column_config.NumberColumn('₽/час', format='%.0f'),
        'reach': st.column_config.NumberColumn('Охват'),
        'clicks': st.column_config.NumberColumn('Клики'),
        'conversions': st.column_config.NumberColumn('Конверсии'),
        'donors_count': st.column_config.NumberColumn('Доноры'),
        'description': st.column_config.TextColumn('Описание', width='large'),
    }
    
    # Редактор
    edited_df = st.data_editor(
        campaigns_df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="campaign_editor"
    )
    
    # Проверка изменений и сохранение
    if not edited_df.equals(campaigns_df):
        from .campaign_data import save_campaigns
        
        if save_campaigns(edited_df):
            st.success("✅ Изменения сохранены")
            st.rerun()
        else:
            st.error("❌ Ошибка сохранения изменений")


def render_campaign_detail_view(campaign_id: str) -> None:
    """
    Детальный просмотр кампании с аналитикой и рекомендациями
    """
    campaign = get_campaign_by_id(campaign_id)
    
    if campaign is None:
        st.error(f"❌ Кампания {campaign_id} не найдена")
        return
    
    # Расчет метрик
    metrics = calculate_campaign_metrics(campaign)
    status_emoji, status_text = get_campaign_status(metrics)
    red_flags = detect_red_flags(metrics, campaign['name'])
    recommendations = generate_recommendations(campaign, red_flags)
    
    # Заголовок
    st.title(f"{status_emoji} {campaign['name']}")
    
    # Базовая информация
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    
    with col_info1:
        st.metric("Статус", status_text)
        st.caption(f"Канал: {campaign['channel']}")
    
    with col_info2:
        st.metric("Прогресс", f"{metrics['progress_percent']:.1f}%")
        st.caption(f"Дней осталось: {metrics['days_remaining']}")
    
    with col_info3:
        st.metric("Собрано", f"{campaign['collected_amount']:,.0f} ₽")
        st.caption(f"Цель: {campaign['target_amount']:,.0f} ₽")
    
    with col_info4:
        delta_color = "normal" if metrics['roi'] >= 250 else "inverse"
        st.metric("ROI", f"{metrics['roi']:.1f}%", 
                 delta=f"{metrics['roi'] - 250:.1f}%")
        st.caption(f"CoF: {metrics['cof']:.2f}")
    
    if campaign['description']:
        st.info(f"📝 **Описание:** {campaign['description']}")
    
    st.divider()
    
    # Красные флаги
    if red_flags:
        st.subheader("🚩 Красные флаги")
        
        for flag in red_flags:
            if flag['severity'] == 'critical':
                st.error(f"**{flag['issue']}**: {flag['description']}")
            else:
                st.warning(f"**{flag['issue']}**: {flag['description']}")
        
        st.divider()
    
    # Рекомендации
    st.subheader("💡 Управленческие рекомендации")
    
    for rec in recommendations:
        st.markdown(f"- {rec}")
    
    st.divider()
    
    # График прогресса
    st.subheader("📈 Динамика сбора")
    st.plotly_chart(render_progress_chart(campaign), use_container_width=True)
    
    # Воронка и метрики
    col_viz1, col_viz2 = st.columns(2)
    
    with col_viz1:
        st.plotly_chart(
            render_funnel_chart(campaign['reach'], campaign['clicks'], campaign['donors_count']),
            use_container_width=True
        )
    
    with col_viz2:
        st.plotly_chart(render_weekly_dynamics(campaign), use_container_width=True)
    
    st.divider()
    
    # Экономический анализ
    render_economic_analysis(campaign)


def export_campaign_report(campaign_id: str, format: str = 'csv') -> Optional[bytes]:
    """
    Экспорт отчета по кампании
    Форматы: csv, excel
    """
    campaign = get_campaign_by_id(campaign_id)
    
    if campaign is None:
        return None
    
    # Расчет метрик
    metrics = calculate_campaign_metrics(campaign)
    
    # Формирование отчета
    report_data = {
        'Параметр': [],
        'Значение': []
    }
    
    # Основная информация
    report_data['Параметр'].extend([
        'ID кампании', 'Название', 'Канал', 'Статус',
        'Дата старта', 'Дата окончания', 'Описание'
    ])
    report_data['Значение'].extend([
        campaign['campaign_id'],
        campaign['name'],
        campaign['channel'],
        campaign['status'],
        str(campaign['start_date']),
        str(campaign['end_date']),
        campaign['description']
    ])
    
    # Финансы
    report_data['Параметр'].extend([
        '', 'ФИНАНСЫ:',
        'Цель сбора (₽)', 'Собрано (₽)', 'Прогресс (%)',
        'Затраты на рекламу (₽)', 'Часы работы', 'Стоимость часа (₽)',
        'Общие затраты (₽)'
    ])
    report_data['Значение'].extend([
        '',
        '',
        campaign['target_amount'],
        campaign['collected_amount'],
        f"{metrics['progress_percent']:.2f}",
        campaign['ad_costs'],
        campaign['labor_hours'],
        campaign['hourly_rate'],
        f"{metrics['total_costs']:.2f}"
    ])
    
    # Метрики
    report_data['Параметр'].extend([
        '', 'МЕТРИКИ:',
        'ROI (%)', 'CoF', 'CTR (%)', 'DCR (%)',
        'Охват', 'Клики', 'Конверсии', 'Доноры',
        'Средний донат (₽)', 'Velocity'
    ])
    report_data['Значение'].extend([
        '',
        '',
        f"{metrics['roi']:.2f}",
        f"{metrics['cof']:.2f}",
        f"{metrics['ctr']:.2f}",
        f"{metrics['dcr']:.2f}",
        campaign['reach'],
        campaign['clicks'],
        campaign['conversions'],
        campaign['donors_count'],
        f"{metrics['avg_donation']:.2f}",
        f"{metrics['velocity']:.2f}"
    ])
    
    df_report = pd.DataFrame(report_data)
    
    # Экспорт
    if format == 'csv':
        return df_report.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_report.to_excel(writer, index=False, sheet_name='Отчет')
        return output.getvalue()
    
    return None


def render_collection_update_form() -> None:
    """
    Форма для инкрементального добавления сборов с историей
    """
    st.subheader("➕ Обновление сборов")
    st.markdown("Добавьте новую собранную сумму. Она автоматически прибавится к текущему сбору.")
    
    campaigns_df = load_campaigns()
    
    if campaigns_df.empty:
        st.info("📭 Нет кампаний. Создайте кампанию сначала.")
        return
    
    # Фильтр только активных кампаний
    active_campaigns = campaigns_df[campaigns_df['status'] == 'active']
    
    if active_campaigns.empty:
        st.warning("⚠️ Нет активных кампаний для обновления")
        return
    
    # Выбор кампании
    campaign_options = {
        row['campaign_id']: f"{row['name']} (текущий сбор: {row['collected_amount']:,.0f} ₽)"
        for _, row in active_campaigns.iterrows()
    }
    
    selected_id = st.selectbox(
        "Выберите кампанию:",
        options=list(campaign_options.keys()),
        format_func=lambda x: campaign_options[x],
        key="collection_update_campaign_select"
    )
    
    if not selected_id:
        return
    
    campaign = get_campaign_by_id(selected_id)
    
    if campaign is None:
        st.error("❌ Кампания не найдена")
        return
    
    st.divider()
    
    # Текущая информация
    col_curr1, col_curr2, col_curr3 = st.columns(3)
    
    with col_curr1:
        st.metric("Текущий сбор", f"{campaign['collected_amount']:,.0f} ₽")
    
    with col_curr2:
        st.metric("Цель", f"{campaign['target_amount']:,.0f} ₽")
    
    with col_curr3:
        remaining = campaign['target_amount'] - campaign['collected_amount']
        st.metric("До цели осталось", f"{remaining:,.0f} ₽")
    
    st.divider()
    
    # Форма добавления
    with st.form("add_collection_form"):
        st.markdown("### 💰 Новое поступление")
        
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            amount_to_add = st.number_input(
                "Сумма поступления (₽) *",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="Сумма, которую нужно добавить к текущему сбору"
            )
        
        with col_form2:
            collection_date = st.date_input(
                "Дата поступления *",
                value=datetime.now().date(),
                help="Когда поступили средства"
            )
        
        note = st.text_area(
            "Примечание (необязательно)",
            placeholder="Например: Перевод от партнёра Х, Сбор через VK Ads и т.д.",
            height=80
        )
        
        # Предпросмотр
        if amount_to_add > 0:
            new_total = campaign['collected_amount'] + amount_to_add
            progress = (new_total / campaign['target_amount'] * 100) if campaign['target_amount'] > 0 else 0
            
            st.info(f"📊 После добавления: **{new_total:,.0f} ₽** ({progress:.1f}% от цели)")
        
        submitted = st.form_submit_button("💾 Добавить сбор", type="primary")
        
        if submitted:
            if amount_to_add <= 0:
                st.error("⚠️ Сумма должна быть больше нуля")
            else:
                result = add_collection_update(
                    campaign_id=selected_id,
                    amount_added=amount_to_add,
                    note=note,
                    update_date=collection_date
                )
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
    
    st.divider()
    
    # История сборов
    st.subheader("📜 История обновлений")
    
    history_df = get_collection_history(selected_id)
    summary = get_collection_summary(selected_id)
    
    if summary:
        # Сводка
        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
        
        with sum_col1:
            st.metric("Всего обновлений", summary['updates_count'])
        
        with sum_col2:
            if summary['last_update_date']:
                st.metric("Последнее обновление", summary['last_update_date'].strftime('%d.%m.%Y'))
            else:
                st.metric("Последнее обновление", "—")
        
        with sum_col3:
            st.metric("Последняя сумма", f"{summary['last_update_amount']:,.0f} ₽")
        
        with sum_col4:
            st.metric("Среднее поступление", f"{summary['average_update']:,.0f} ₽")
    
    if not history_df.empty:
        st.divider()
        
        # Визуализация истории
        viz_col1, viz_col2 = st.columns([2, 1])
        
        with viz_col1:
            # График накопительной суммы
            import plotly.graph_objects as go
            
            # Сортируем по дате
            history_sorted = history_df.sort_values('update_date')
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=history_sorted['update_date'],
                y=history_sorted['total_after_update'],
                mode='lines+markers',
                name='Накопительная сумма',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=8),
                fill='tozeroy'
            ))
            
            # Целевая линия
            fig.add_hline(
                y=campaign['target_amount'],
                line_dash="dash",
                line_color="#10b981",
                annotation_text=f"Цель: {campaign['target_amount']:,.0f} ₽"
            )
            
            fig.update_layout(
                title="Динамика сборов",
                xaxis_title="Дата",
                yaxis_title="Сумма (₽)",
                height=350,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with viz_col2:
            # Столбчатая диаграмма поступлений
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                x=history_sorted['update_date'].astype(str),
                y=history_sorted['amount_added'],
                marker_color='#8b5cf6',
                text=history_sorted['amount_added'].apply(lambda x: f"{x:,.0f}"),
                textposition='auto'
            ))
            
            fig2.update_layout(
                title="Поступления",
                xaxis_title="Дата",
                yaxis_title="Сумма (₽)",
                height=350,
                showlegend=False
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        
        # Таблица истории
        st.markdown("**Детальная история:**")
        
        display_history = history_df.copy()
        display_history['update_date'] = pd.to_datetime(display_history['update_date']).dt.strftime('%d.%m.%Y')
        display_history['amount_added'] = display_history['amount_added'].apply(lambda x: f"+{x:,.0f} ₽")
        display_history['total_after_update'] = display_history['total_after_update'].apply(lambda x: f"{x:,.0f} ₽")
        
        # Оставляем только нужные колонки
        display_history = display_history[['update_date', 'amount_added', 'total_after_update', 'note']]
        display_history.columns = ['Дата', 'Добавлено', 'Итого', 'Примечание']
        
        st.dataframe(
            display_history,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📭 История обновлений пуста. Добавьте первое поступление выше.")


def render_multi_channel_dashboard() -> None:
    """
    Дашборд мультиканальности (анализ по группам)
    """
    st.subheader("🌐 Мультиканальная аналитика")
    st.markdown("Анализ эффективности групп кампаний, запущенных в разных каналах.")
    
    campaigns_df = load_campaigns()
    
    if campaigns_df.empty:
        st.info("📭 Нет данных.")
        return
        
    if 'group_id' not in campaigns_df.columns:
        st.info("📭 Нет данных о группах. Отредактируйте кампании и добавьте им группу.")
        return
        
    groups = campaigns_df['group_id'].dropna().unique().tolist()
    
    if not groups:
        st.info("📭 Нет созданных групп. Добавьте группу при создании или редактировании кампании.")
        return
        
    # Выбор группы
    selected_group = st.selectbox("Выберите группу кампаний:", groups)
    
    if selected_group:
        # Фильтруем кампании группы
        group_df = campaigns_df[campaigns_df['group_id'] == selected_group]
        
        st.divider()
        
        # Агрегированные метрики
        total_collected = group_df['collected_amount'].sum()
        total_target = group_df['target_amount'].sum()
        total_costs = group_df['ad_costs'].sum() + (group_df['labor_hours'] * group_df['hourly_rate']).sum()
        
        # Средние метрики (взвешенные или простые)
        avg_roi = ((total_collected - total_costs) / total_costs * 100) if total_costs > 0 else 0
        avg_cof = (total_costs / total_collected) if total_collected > 0 else 0
        
        # Отображение KPI группы
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.metric("Всего собрано", f"{total_collected:,.0f} ₽")
        with kpi2:
            progress = (total_collected / total_target * 100) if total_target > 0 else 0
            st.metric("Общий прогресс", f"{progress:.1f}%")
        with kpi3:
            delta_color = "normal" if avg_roi >= 250 else "inverse"
            st.metric("Общий ROI", f"{avg_roi:.1f}%", delta=f"{avg_roi - 250:.1f}%")
        with kpi4:
            st.metric("Общий CoF", f"{avg_cof:.2f}")
            
        st.divider()
        
        # Сравнение каналов внутри группы
        st.subheader("📊 Вклад каналов в результат")
        
        import plotly.express as px
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Pie chart сборов
            fig_pie = px.pie(
                group_df, 
                values='collected_amount', 
                names='channel', 
                title='Доля сборов по каналам',
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_chart2:
            # Bar chart ROI
            # Рассчитываем ROI для каждой кампании
            group_df['total_costs'] = group_df['ad_costs'] + (group_df['labor_hours'] * group_df['hourly_rate'])
            group_df['roi'] = group_df.apply(
                lambda x: ((x['collected_amount'] - x['total_costs']) / x['total_costs'] * 100) if x['total_costs'] > 0 else 0, 
                axis=1
            )
            
            fig_bar = px.bar(
                group_df,
                x='channel',
                y='roi',
                title='ROI по каналам',
                color='roi',
                color_continuous_scale='RdYlGn',
                text_auto='.1f'
            )
            # Линия отсечения 250%
            fig_bar.add_hline(y=250, line_dash="dash", line_color="red", annotation_text="Target 250%")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # Детальная таблица
        st.subheader("📋 Детализация")
        
        display_df = group_df[['name', 'channel', 'collected_amount', 'target_amount', 'roi', 'status']].copy()
        display_df['collected_amount'] = display_df['collected_amount'].apply(lambda x: f"{x:,.0f} ₽")
        display_df['target_amount'] = display_df['target_amount'].apply(lambda x: f"{x:,.0f} ₽")
        display_df['roi'] = display_df['roi'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)


