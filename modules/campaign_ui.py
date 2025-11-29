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
    load_campaigns
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
