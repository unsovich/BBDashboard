"""
Модули для дашборда Синяя Птица
"""

from .campaign_data import (
    load_campaigns,
    save_campaigns,
    add_campaign,
    update_campaign,
    delete_campaign,
    get_campaign_by_id
)

from .campaign_analytics import (
    calculate_roi,
    calculate_cof,
    calculate_ctr,
    calculate_dcr,
    calculate_velocity,
    calculate_campaign_metrics,
    get_campaign_status,
    detect_red_flags,
    generate_recommendations
)

from .campaign_viz import (
    render_campaign_summary_table,
    render_progress_chart,
    render_weekly_dynamics,
    render_funnel_chart,
    render_channel_comparison,
    render_economic_analysis
)

from .campaign_ui import (
    render_campaign_input_form,
    render_campaign_editor,
    render_campaign_detail_view,
    export_campaign_report,
    render_collection_update_form,
    render_multi_channel_dashboard
)

from .program_financials import (
    load_financials,
    save_financials,
    add_financial_record,
    get_financial_record,
    get_latest_financial_record,
    get_financial_data_with_fallback,
    get_program_history,
    delete_financial_record,
    get_aggregated_financials,
    calculate_profitability,
    PROGRAMS
)

__all__ = [
    # Data
    'load_campaigns',
    'save_campaigns',
    'add_campaign',
    'update_campaign',
    'delete_campaign',
    'get_campaign_by_id',
    # Analytics
    'calculate_roi',
    'calculate_cof',
    'calculate_ctr',
    'calculate_dcr',
    'calculate_velocity',
    'calculate_campaign_metrics',
    'get_campaign_status',
    'detect_red_flags',
    'generate_recommendations',
    # Visualization
    'render_campaign_summary_table',
    'render_progress_chart',
    'render_weekly_dynamics',
    'render_funnel_chart',
    'render_channel_comparison',
    'render_economic_analysis',
    # UI
    'render_campaign_input_form',
    'render_campaign_editor',
    'render_campaign_detail_view',
    'export_campaign_report',
    'render_collection_update_form',
    'render_multi_channel_dashboard',
]
