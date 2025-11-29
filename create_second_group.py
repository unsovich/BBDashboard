"""
Скрипт для создания ВТОРОЙ тестовой группы кампаний
"""

import sys
import os
from datetime import date

# Add current directory to path
sys.path.append(os.getcwd())

from modules.campaign_data import add_campaign

# Группа "Летний лагерь 2026"
group_name = "Летний лагерь 2026"

campaigns = [
    {
        'name': 'Лагерь - VK',
        'channel': 'VK',
        'group_id': group_name,
        'start_date': date(2026, 6, 1),
        'end_date': date(2026, 8, 31),
        'target_amount': 200000,
        'collected_amount': 0,
        'ad_costs': 0,
        'labor_hours': 0,
        'description': 'Сбор на лагерь'
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

print("\nГотово! Вторая группа создана.")
