import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

print("Attempting imports...")

try:
    print("Importing campaign_data...")
    from modules import campaign_data
    print("✅ campaign_data imported")
except Exception as e:
    print(f"❌ campaign_data failed: {e}")

try:
    print("Importing campaign_analytics...")
    from modules import campaign_analytics
    print("✅ campaign_analytics imported")
except Exception as e:
    print(f"❌ campaign_analytics failed: {e}")

try:
    print("Importing campaign_viz...")
    from modules import campaign_viz
    print("✅ campaign_viz imported")
except Exception as e:
    print(f"❌ campaign_viz failed: {e}")

try:
    print("Importing campaign_ui...")
    from modules import campaign_ui
    print("✅ campaign_ui imported")
except Exception as e:
    print(f"❌ campaign_ui failed: {e}")

try:
    print("Importing from modules package...")
    from modules.campaign_ui import render_collection_update_form
    print("✅ render_collection_update_form imported")
except Exception as e:
    print(f"❌ render_collection_update_form import failed: {e}")
