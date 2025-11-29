import sys
import os
import pandas as pd

# Add current directory to path
sys.path.append(os.getcwd())

from modules.campaign_data import load_campaigns, get_campaign_groups

print("--- Debugging Campaign Groups ---")

# 1. Load dataframe
df = load_campaigns()
print(f"Total campaigns: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# 2. Check group_id column
if 'group_id' in df.columns:
    print("\n'group_id' column exists.")
    print(f"Unique groups in DB: {df['group_id'].unique()}")
    print(f"Null values in group_id: {df['group_id'].isnull().sum()}")
else:
    print("\n❌ 'group_id' column MISSING in DataFrame!")

# 3. Test get_campaign_groups()
groups = get_campaign_groups()
print(f"\nResult of get_campaign_groups(): {groups}")

# 4. Check specific test data
if not df.empty and 'group_id' in df.columns:
    test_group = df[df['group_id'] == "Новогодний марафон 2025"]
    print(f"\nCampaigns in 'Новогодний марафон 2025': {len(test_group)}")
