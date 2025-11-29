"""
Скрипт для создания тестовых данных кампаний
"""

import sys
sys.path.append('/Users/unsovich/AntigravityProjects/BBDashboard')

from modules.campaign_data import add_campaign
from datetime import date, timedelta

# Создаем несколько тестовых кампаний
campaigns = [
    {
        'name': 'Новогодний сбор VK',
        'channel': 'VK',
        'start_date': date(2025, 11, 1),
        'end_date': date(2025, 12, 31),
        'target_amount': 500000,
        'collected_amount': 320000,
        'ad_costs': 25000,
        'labor_hours': 80,
        'reach': 150000,
        'clicks': 4500,
        'conversions': 250,
        'donors_count': 180,
        'description': 'Новогодняя кампания по сбору средств через VK Ads'
    },
    {
        'name': 'Email рассылка - Помощь детям',
        'channel': 'Email',
        'start_date': date(2025, 10, 15),
        'end_date': date(2025, 11, 15),
        'target_amount': 200000,
        'collected_amount': 245000,
        'ad_costs': 5000,
        'labor_hours': 40,
        'reach': 25000,
        'clicks': 1250,
        'conversions': 180,
        'donors_count': 120,
        'description': 'Целевая рассылка подписчикам о программе помощи детям',
        'status': 'completed'
    },
    {
        'name': 'Telegram канал - Сбор на лечение',
        'channel': 'Telegram',
        'start_date': date(2025, 11, 15),
        'end_date': date(2025, 12, 15),
        'target_amount': 300000,
        'collected_amount': 85000,
        'ad_costs': 15000,
        'labor_hours': 30,
        'reach': 80000,
        'clicks': 800,
        'conversions': 65,
        'donors_count': 42,
        'description': 'Сбор через Telegram на срочное лечение'
    },
    {
        'name': 'Партнёрская программа - Корпорации',
        'channel': 'Партнёры',
        'start_date': date(2025, 9, 1),
        'end_date': date(2025, 12, 31),
        'target_amount': 1000000,
        'collected_amount': 680000,
        'ad_costs': 10000,
        'labor_hours': 120,
        'reach': 50,
        'clicks': 35,
        'conversions': 12,
        'donors_count': 8,
        'description': 'Корпоративная программа партнёрства с крупными компаниями'
    },
]

print("Создание тестовых кампаний...")
for camp in campaigns:
    result = add_campaign(**camp)
    if result['success']:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")

print("\nГотово! Тестовые данные созданы.")
