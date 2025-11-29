"""
Модуль аналитики кампаний
Бизнес-логика расчета метрик, определения красных флагов и рекомендаций
"""

import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any


# --- КОНСТАНТЫ ДЛЯ КРАСНЫХ ФЛАГОВ ---
ROI_CRITICAL_THRESHOLD = 2.5      # ROI < 2.5 → Критично (остановка)
ROI_WARNING_THRESHOLD = 3.5       # ROI < 3.5 → Требует внимания
CTR_LOW_THRESHOLD = 1.0           # CTR < 1% → Проблема с каналом
DCR_LOW_THRESHOLD = 2.0           # DCR < 2% → Проблема с impact
VELOCITY_WARNING = 0.8            # Темп < 80% от плана → Диверсификация


# --- БАЗОВЫЕ МЕТРИКИ ---

def calculate_roi(revenue: float, costs: float) -> float:
    """
    ROI фандрайзинга = (Revenue - Costs) / Costs * 100
    Возвращает ROI в процентах
    """
    if costs <= 0:
        return 0.0
    return ((revenue - costs) / costs) * 100


def calculate_cof(costs: float, revenue: float) -> float:
    """
    Cost of Fundraising = Costs / Revenue
    Стоимость привлечения 1 рубля
    """
    if revenue <= 0:
        return 0.0
    return costs / revenue


def calculate_ctr(clicks: int, reach: int) -> float:
    """
    Click-Through Rate = (Clicks / Reach) * 100
    Процент кликнувших от охвата
    """
    if reach <= 0:
        return 0.0
    return (clicks / reach) * 100


def calculate_dcr(donors: int, clicks: int) -> float:
    """
    Donor Conversion Rate = (Donors / Clicks) * 100
    Процент ставших донорами от кликнувших
    """
    if clicks <= 0:
        return 0.0
    return (donors / clicks) * 100


def calculate_velocity(
    current_amount: float,
    target_amount: float,
    days_passed: int,
    total_days: int
) -> float:
    """
    Velocity - темп сбора относительно плана
    Возвращает коэффициент (1.0 = точно по плану, >1 = опережение, <1 = отставание)
    """
    if total_days <= 0 or target_amount <= 0:
        return 0.0
    
    # Ожидаемый прогресс на текущий момент
    expected_progress = (days_passed / total_days) * target_amount
    
    if expected_progress <= 0:
        return 0.0
    
    # Фактический прогресс относительно ожидаемого
    velocity = current_amount / expected_progress
    
    return velocity


def calculate_average_donation(collected_amount: float, donors_count: int) -> float:
    """Средний донат"""
    if donors_count <= 0:
        return 0.0
    return collected_amount / donors_count


def calculate_total_costs(ad_costs: float, labor_hours: float, hourly_rate: float) -> float:
    """Общие затраты = Реклама + Трудозатраты"""
    return ad_costs + (labor_hours * hourly_rate)


# --- КОМПЛЕКСНЫЙ РАСЧЕТ МЕТРИК ---

def calculate_campaign_metrics(campaign: pd.Series) -> Dict[str, float]:
    """
    Рассчитывает все метрики для кампании
    Принимает Series с данными кампании
    Возвращает словарь с расчетными метриками
    """
    # Извлекаем базовые данные
    collected = float(campaign.get('collected_amount', 0))
    target = float(campaign.get('target_amount', 0))
    ad_costs = float(campaign.get('ad_costs', 0))
    labor_hours = float(campaign.get('labor_hours', 0))
    hourly_rate = float(campaign.get('hourly_rate', 500))
    reach = int(campaign.get('reach', 0))
    clicks = int(campaign.get('clicks', 0))
    conversions = int(campaign.get('conversions', 0))
    donors = int(campaign.get('donors_count', 0))
    
    # Даты
    start_date = campaign.get('start_date')
    end_date = campaign.get('end_date')
    today = datetime.now().date()
    
    # Расчет дней
    if isinstance(start_date, pd.Timestamp):
        start_date = start_date.date()
    if isinstance(end_date, pd.Timestamp):
        end_date = end_date.date()
    
    if start_date and end_date:
        total_days = (end_date - start_date).days + 1
        days_passed = min((today - start_date).days + 1, total_days)
    else:
        total_days = 0
        days_passed = 0
    
    # Рассчитываем метрики
    total_costs = calculate_total_costs(ad_costs, labor_hours, hourly_rate)
    
    metrics = {
        'total_costs': total_costs,
        'roi': calculate_roi(collected, total_costs),
        'cof': calculate_cof(total_costs, collected),
        'ctr': calculate_ctr(clicks, reach),
        'dcr': calculate_dcr(donors, clicks),
        'velocity': calculate_velocity(collected, target, days_passed, total_days),
        'avg_donation': calculate_average_donation(collected, donors),
        'progress_percent': (collected / target * 100) if target > 0 else 0,
        'days_passed': days_passed,
        'days_total': total_days,
        'days_remaining': max(0, total_days - days_passed)
    }
    
    return metrics


# --- ОПРЕДЕЛЕНИЕ СТАТУСА ---

def get_campaign_status(metrics: Dict[str, float]) -> Tuple[str, str]:
    """
    Определяет статус кампании на основе метрик
    Возвращает (emoji, text_status)
    
    Статусы:
    - 🚨 Критично (ROI < 2.5)
    - ⚠️ Внимание (ROI < 3.5 или другие проблемы)
    - ✅ Норма (все в порядке)
    """
    roi = metrics.get('roi', 0)
    ctr = metrics.get('ctr', 0)
    dcr = metrics.get('dcr', 0)
    velocity = metrics.get('velocity', 0)
    
    # Критичные проблемы
    if roi < ROI_CRITICAL_THRESHOLD * 100:  # ROI в процентах
        return "🚨", "Критично"
    
    # Предупреждения
    warning_conditions = [
        roi < ROI_WARNING_THRESHOLD * 100,
        ctr < CTR_LOW_THRESHOLD,
        dcr < DCR_LOW_THRESHOLD,
        velocity < VELOCITY_WARNING
    ]
    
    if any(warning_conditions):
        return "⚠️", "Внимание"
    
    # Все в норме
    return "✅", "Норма"


# --- КРАСНЫЕ ФЛАГИ ---

def detect_red_flags(metrics: Dict[str, float], campaign_name: str = "") -> List[Dict[str, str]]:
    """
    Определяет красные флаги для кампании
    Возвращает список словарей с описанием проблем
    Каждый флаг: {'severity': 'critical'|'warning', 'issue': str, 'description': str}
    """
    flags = []
    
    roi = metrics.get('roi', 0)
    ctr = metrics.get('ctr', 0)
    dcr = metrics.get('dcr', 0)
    velocity = metrics.get('velocity', 0)
    
    # Критичный ROI
    if roi < ROI_CRITICAL_THRESHOLD * 100:
        flags.append({
            'severity': 'critical',
            'issue': f'Критически низкий ROI ({roi:.1f}%)',
            'description': f'ROI < {ROI_CRITICAL_THRESHOLD*100}%. Рекомендуется немедленная остановка кампании.'
        })
    # Низкий ROI (предупреждение)
    elif roi < ROI_WARNING_THRESHOLD * 100:
        flags.append({
            'severity': 'warning',
            'issue': f'Низкий ROI ({roi:.1f}%)',
            'description': f'ROI < {ROI_WARNING_THRESHOLD*100}%. Требуется оптимизация кампании.'
        })
    
    # Низкий CTR
    if ctr < CTR_LOW_THRESHOLD and ctr > 0:
        flags.append({
            'severity': 'warning',
            'issue': f'Низкий CTR ({ctr:.2f}%)',
            'description': 'Проблема с каналом или креативами. Нужна оптимизация таргетинга и контента.'
        })
    
    # Низкий DCR
    if dcr < DCR_LOW_THRESHOLD and dcr > 0:
        flags.append({
            'severity': 'warning',
            'issue': f'Низкий DCR ({dcr:.2f}%)',
            'description': 'Проблема с доказательной базой Impact. Усильте социальное доказательство.'
        })
    
    # Низкий темп сбора
    if velocity < VELOCITY_WARNING and velocity > 0:
        flags.append({
            'severity': 'warning',
            'issue': f'Отставание от плана (темп {velocity*100:.0f}%)',
            'description': 'Требуется диверсификация каналов и усиление маркетинга.'
        })
    
    return flags


# --- РЕКОМЕНДАЦИИ ---

def generate_recommendations(campaign: pd.Series, red_flags: List[Dict[str, str]]) -> List[str]:
    """
    Генерирует управленческие рекомендации на основе красных флагов
    Возвращает список рекомендаций
    """
    recommendations = []
    
    if not red_flags:
        recommendations.append("✅ Кампания идёт хорошо. Продолжайте текущую стратегию.")
        return recommendations
    
    # Анализируем флаги и даём рекомендации
    critical_flags = [f for f in red_flags if f['severity'] == 'critical']
    warning_flags = [f for f in red_flags if f['severity'] == 'warning']
    
    # Критичные проблемы
    if critical_flags:
        recommendations.append("🚨 КРИТИЧНО: Рассмотрите немедленную остановку кампании")
        recommendations.append("📊 Проведите детальный анализ затрат и эффективности каналов")
    
    # Проблемы с каналом (CTR)
    if any('CTR' in f['issue'] for f in warning_flags):
        recommendations.append("🎯 Оптимизируйте таргетинг и креативы")
        recommendations.append("📝 Проведите A/B тестирование рекламных материалов")
    
    # Проблемы с конверсией (DCR)
    if any('DCR' in f['issue'] for f in warning_flags):
        recommendations.append("💡 Усильте доказательную базу Impact (истории, цифры, отзывы)")
        recommendations.append("🎥 Добавьте визуальный контент и эмоциональные истории")
    
    # Проблемы с темпом
    if any('темп' in f['issue'].lower() for f in warning_flags):
        recommendations.append("🔄 Диверсифицируйте каналы привлечения")
        recommendations.append("📧 Активируйте дополнительные каналы (email, партнёры)")
    
    # Общие рекомендации
    if any('ROI' in f['issue'] for f in warning_flags):
        recommendations.append("💰 Пересмотрите структуру затрат на кампанию")
        recommendations.append("⏸️ Приостановите неэффективные каналы")
    
    return recommendations


# --- СРАВНИТЕЛЬНЫЙ АНАЛИЗ ---

def compare_channels(campaigns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Сравнительный анализ эффективности каналов
    Возвращает DataFrame с агрегированными метриками по каналам
    """
    if campaigns_df.empty:
        return pd.DataFrame()
    
    # Группируем по каналам
    channels = []
    
    for channel in campaigns_df['channel'].unique():
        channel_campaigns = campaigns_df[campaigns_df['channel'] == channel]
        
        total_collected = channel_campaigns['collected_amount'].sum()
        total_ad_costs = channel_campaigns['ad_costs'].sum()
        total_labor_hours = channel_campaigns['labor_hours'].sum()
        avg_hourly_rate = channel_campaigns['hourly_rate'].mean()
        
        total_costs = total_ad_costs + (total_labor_hours * avg_hourly_rate)
        
        total_reach = channel_campaigns['reach'].sum()
        total_clicks = channel_campaigns['clicks'].sum()
        total_donors = channel_campaigns['donors_count'].sum()
        
        channels.append({
            'channel': channel,
            'campaigns_count': len(channel_campaigns),
            'total_collected': total_collected,
            'total_costs': total_costs,
            'avg_roi': calculate_roi(total_collected, total_costs),
            'avg_cof': calculate_cof(total_costs, total_collected),
            'avg_ctr': calculate_ctr(total_clicks, total_reach),
            'avg_dcr': calculate_dcr(total_donors, total_clicks),
            'total_donors': total_donors,
            'avg_donation': calculate_average_donation(total_collected, total_donors)
        })
    
    return pd.DataFrame(channels)
