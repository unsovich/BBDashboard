"""
Скрипт для создания тестовых мультиканальных кампаний
"""

import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from modules.campaign_data import add_campaign
from datetime import date

# Группа "Новогодний марафон 2025"
group_name = "Новогодний марафон 2025"

campaigns = [
    {
        'name': 'НГ Марафон - VK',
        'channel': 'VK',
        'group_id': group_name,
        'start_date': date(2025, 12, 1),
        'end_date': date(2025, 12, 31),
        'target_amount': 100000,
        'collected_amount': 45000,
        'ad_costs': 5000,
        'labor_hours': 10,
        'description': 'Таргет в ВК'
    },
    {
        'name': 'НГ Марафон - Telegram',
        'channel': 'Telegram',
        'group_id': group_name,
        'start_date': date(2025, 12, 1),
        'end_date': date(2025, 12, 31),
        'target_amount': 150000,
        'collected_amount': 80000,
        'ad_costs': 10000,
        'labor_hours': 15,
        'description': 'Посевы в каналах'
    },
    {
        'name': 'НГ Марафон - Email',
        'channel': 'Email',
        'group_id': group_name,
        'start_date': date(2025, 12, 1),
        'end_date': date(2025, 12, 31),
        'target_amount': 50000,
        'collected_amount': 60000,
        'ad_costs': 0,
        'labor_hours': 5,
        'description': 'Рассылка по базе'
    }
]

print(f"Создание кампаний для группы '{group_name}'...")

for camp in campaigns:
    try:
        result = add_campaign(**camp)
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\nГотово! Тестовые данные созданы.")
