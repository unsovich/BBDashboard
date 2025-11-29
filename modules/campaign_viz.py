"""
Модуль визуализации кампаний
Отвечает за создание графиков, таблиц и визуальных компонентов
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .campaign_analytics import (
    calculate_campaign_metrics,
    get_campaign_status,
    compare_channels
)


# --- ЦВЕТОВАЯ ПАЛИТРА ---
COLORS = {
    'success': '#10b981',      # Зеленый
    'warning': '#f59e0b',      # Оранжевый
    'critical': '#ef4444',     # Красный
    'primary': '#3b82f6',      # Синий
    'secondary': '#6b7280',    # Серый
    'target': '#8b5cf6',       # Фиолетовый
}


def render_campaign_summary_table(campaigns_df: pd.DataFrame) -> None:
    """
    Отображает сводную таблицу всех кампаний со статусами и ключевыми метриками
    """
    if campaigns_df.empty:
        st.info("📭 Нет активных кампаний. Создайте новую кампанию для начала мониторинга.")
        return
    
    # Подготовка данных для таблицы
    summary_data = []
    
    for _, campaign in campaigns_df.iterrows():
        metrics = calculate_campaign_metrics(campaign)
        status_emoji, status_text = get_campaign_status(metrics)
        
        summary_data.append({
            'Статус': f"{status_emoji} {status_text}",
            'Название': campaign['name'],
            'Канал': campaign['channel'],
            'Прогресс': f"{metrics['progress_percent']:.1f}%",
            'Собрано': f"{campaign['collected_amount']:,.0f} ₽",
            'Цель': f"{campaign['target_amount']:,.0f} ₽",
            'ROI': f"{metrics['roi']:.1f}%",
            'CoF': f"{metrics['cof']:.2f}",
            'CTR': f"{metrics['ctr']:.2f}%",
            'DCR': f"{metrics['dcr']:.2f}%",
            'Дней осталось': metrics['days_remaining'],
            'ID': campaign['campaign_id']
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Конфигурация колонок для отображения
    column_config = {
        'Статус': st.column_config.TextColumn('Статус', width='small'),
        'Название': st.column_config.TextColumn('Название кампании', width='medium'),
        'Канал': st.column_config.TextColumn('Канал', width='small'),
        'Прогресс': st.column_config.TextColumn('Прогресс', width='small'),
        'Собрано': st.column_config.TextColumn('Собрано', width='small'),
        'Цель': st.column_config.TextColumn('Цель', width='small'),
        'ROI': st.column_config.TextColumn('ROI', width='small'),
        'CoF': st.column_config.TextColumn('CoF', width='small'),
        'CTR': st.column_config.TextColumn('CTR', width='small'),
        'DCR': st.column_config.TextColumn('DCR', width='small'),
        'Дней осталось': st.column_config.NumberColumn('Осталось', width='small'),
        'ID': st.column_config.TextColumn('ID', width='small'),
    }
    
    # Отображение таблицы
    st.dataframe(
        summary_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )


def render_progress_chart(campaign: pd.Series) -> go.Figure:
    """
    График прогресса сбора vs целевая траектория
    Показывает фактический прогресс и линейную целевую траекторию
    """
    metrics = calculate_campaign_metrics(campaign)
    
    start_date = campaign['start_date']
    end_date = campaign['end_date']
    target_amount = campaign['target_amount']
    collected_amount = campaign['collected_amount']
    
    # Конвертируем даты
    if isinstance(start_date, pd.Timestamp):
        start_date = start_date.date()
    if isinstance(end_date, pd.Timestamp):
        end_date = end_date.date()
    
    # Создаем временную шкалу
    total_days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(total_days + 1)]
    
    # Целевая траектория (линейная)
    target_trajectory = [target_amount * (i / total_days) for i in range(total_days + 1)]
    
    # Фактический прогресс (упрощенно - только текущая точка)
    today = datetime.now().date()
    days_passed = min((today - start_date).days, total_days)
    
    # Создаем график
    fig = go.Figure()
    
    # Целевая траектория
    fig.add_trace(go.Scatter(
        x=dates,
        y=target_trajectory,
        name='Целевая траектория',
        line=dict(color=COLORS['target'], dash='dash', width=2),
        mode='lines'
    ))
    
    # Фактический прогресс
    actual_dates = [start_date, start_date + timedelta(days=days_passed)]
    actual_values = [0, collected_amount]
    
    fig.add_trace(go.Scatter(
        x=actual_dates,
        y=actual_values,
        name='Фактический прогресс',
        line=dict(color=COLORS['primary'], width=3),
        mode='lines+markers',
        marker=dict(size=8)
    ))
    
    # Целевая сумма
    fig.add_hline(
        y=target_amount,
        line_dash="dot",
        line_color=COLORS['success'],
        annotation_text=f"Цель: {target_amount:,.0f} ₽"
    )
    
    fig.update_layout(
        title=f"Прогресс кампании: {campaign['name']}",
        xaxis_title="Дата",
        yaxis_title="Сумма сбора (₽)",
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def render_weekly_dynamics(campaign: pd.Series) -> go.Figure:
    """
    Недельная динамика ключевых метрик
    TODO: Требуется историческая таблица с недельными срезами
    Пока показываем текущие метрики
    """
    metrics = calculate_campaign_metrics(campaign)
    
    # Упрощенная версия - текущие метрики в виде столбцов
    metric_names = ['ROI (%)', 'CTR (%)', 'DCR (%)']
    metric_values = [
        metrics['roi'],
        metrics['ctr'],
        metrics['dcr']
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=metric_names,
        y=metric_values,
        marker_color=[COLORS['success'], COLORS['primary'], COLORS['warning']],
        text=[f"{v:.2f}" for v in metric_values],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Текущие показатели эффективности",
        yaxis_title="Значение",
        height=350,
        showlegend=False
    )
    
    return fig


def render_funnel_chart(reach: int, clicks: int, donors: int) -> go.Figure:
    """
    Воронка конверсий: Охват → Клики → Доноры
    """
    stages = ['Охват', 'Клики', 'Доноры']
    values = [reach, clicks, donors]
    
    # Расчет конверсий на каждом этапе
    percentages = []
    if reach > 0:
        percentages.append(100)
        percentages.append((clicks / reach) * 100 if reach > 0 else 0)
        percentages.append((donors / reach) * 100 if reach > 0 else 0)
    else:
        percentages = [0, 0, 0]
    
    fig = go.Figure()
    
    fig.add_trace(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(
            color=[COLORS['primary'], COLORS['warning'], COLORS['success']]
        ),
        connector=dict(line=dict(color=COLORS['secondary'], width=2))
    ))
    
    fig.update_layout(
        title="Воронка конверсий",
        height=400,
        showlegend=False
    )
    
    return fig


def render_channel_comparison(campaigns_df: pd.DataFrame) -> go.Figure:
    """
    Сравнительный анализ эффективности каналов
    """
    channels_data = compare_channels(campaigns_df)
    
    if channels_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Нет данных для сравнения",
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Создаем grouped bar chart для сравнения метрик по каналам
    fig = go.Figure()
    
    # ROI
    fig.add_trace(go.Bar(
        name='ROI (%)',
        x=channels_data['channel'],
        y=channels_data['avg_roi'],
        marker_color=COLORS['success']
    ))
    
    # CTR
    fig.add_trace(go.Bar(
        name='CTR (%)',
        x=channels_data['channel'],
        y=channels_data['avg_ctr'],
        marker_color=COLORS['primary']
    ))
    
    # DCR
    fig.add_trace(go.Bar(
        name='DCR (%)',
        x=channels_data['channel'],
        y=channels_data['avg_dcr'],
        marker_color=COLORS['warning']
    ))
    
    fig.update_layout(
        title="Сравнение эффективности каналов",
        xaxis_title="Канал",
        yaxis_title="Значение (%)",
        barmode='group',
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def render_economic_analysis(campaign: pd.Series) -> None:
    """
    Блок экономического анализа (ФАЭП-3)
    Input → Process → Output
    """
    metrics = calculate_campaign_metrics(campaign)
    
    st.subheader("💰 Экономический анализ (ФАЭП-3)")
    
    # Input
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Input (Затраты)**")
        st.metric("Реклама", f"{campaign['ad_costs']:,.0f} ₽")
        st.metric("Персонал", f"{campaign['labor_hours']:.1f} ч")
        st.metric("Стоимость часа", f"{campaign['hourly_rate']:.0f} ₽")
        st.metric("**Всего затрат**", f"{metrics['total_costs']:,.0f} ₽")
    
    with col2:
        st.markdown("**⚙️ Process (Активность)**")
        st.metric("Охват", f"{campaign['reach']:,}")
        st.metric("Клики", f"{campaign['clicks']:,}")
        st.metric("Конверсии", f"{campaign['conversions']:,}")
        st.metric("Доноры", f"{campaign['donors_count']:,}")
    
    with col3:
        st.markdown("**💎 Output (Результат)**")
        st.metric("Собрано", f"{campaign['collected_amount']:,.0f} ₽")
        st.metric("ROI", f"{metrics['roi']:.1f}%", 
                 delta=f"{metrics['roi'] - 250:.1f}%" if metrics['roi'] > 0 else None)
        st.metric("CoF", f"{metrics['cof']:.2f}")
        st.metric("Средний донат", f"{metrics['avg_donation']:,.0f} ₽")
    
    # Визуализация потока
    st.divider()
    
    flow_col1, flow_col2 = st.columns([2, 1])
    
    with flow_col1:
        # Sankey diagram для потока
        fig = go.Figure(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=["Затраты", "Охват", "Клики", "Доноры", "Доход"],
                color=[COLORS['critical'], COLORS['secondary'], COLORS['primary'], 
                       COLORS['warning'], COLORS['success']]
            ),
            link=dict(
                source=[0, 1, 2, 3],
                target=[1, 2, 3, 4],
                value=[
                    metrics['total_costs'],
                    campaign['clicks'],
                    campaign['donors_count'],
                    campaign['collected_amount']
                ]
            )
        ))
        
        fig.update_layout(
            title="Поток ценности",
            height=300,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with flow_col2:
        st.markdown("**📈 Ключевые коэффициенты**")
        
        # Рентабельность
        profitability = ((campaign['collected_amount'] - metrics['total_costs']) / 
                        campaign['collected_amount'] * 100) if campaign['collected_amount'] > 0 else 0
        
        st.metric("Рентабельность", f"{profitability:.1f}%")
        st.metric("Конверсия Reach→Click", f"{metrics['ctr']:.2f}%")
        st.metric("Конверсия Click→Donor", f"{metrics['dcr']:.2f}%")
        
        # Общая конверсия
        total_conversion = (campaign['donors_count'] / campaign['reach'] * 100) if campaign['reach'] > 0 else 0
        st.metric("Общая конверсия", f"{total_conversion:.3f}%")
