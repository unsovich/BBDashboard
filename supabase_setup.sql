-- ==================================================
-- SUPABASE DATABASE SETUP SCRIPT
-- АНО «Синяя птица» - KPI Dashboard
-- ==================================================

-- Включаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================================================
-- 1. ТАБЛИЦА: kpi_history
-- Хранит историю KPI показателей
-- ==================================================

CREATE TABLE IF NOT EXISTS kpi_history (
    id BIGSERIAL PRIMARY KEY,
    date_start DATE NOT NULL,
    date_end DATE,
    week_year VARCHAR(10),
    date_range VARCHAR(50),
    category VARCHAR(100) NOT NULL,
    kpi_id VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    minimum DECIMAL,
    target DECIMAL,
    actual DECIMAL,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для kpi_history
CREATE INDEX IF NOT EXISTS idx_kpi_date_start ON kpi_history(date_start);
CREATE INDEX IF NOT EXISTS idx_kpi_date_end ON kpi_history(date_end);
CREATE INDEX IF NOT EXISTS idx_kpi_category ON kpi_history(category);
CREATE INDEX IF NOT EXISTS idx_kpi_id ON kpi_history(kpi_id);
CREATE INDEX IF NOT EXISTS idx_kpi_created ON kpi_history(created_at);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_kpi_history_updated_at BEFORE UPDATE ON kpi_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================================================
-- 2. ТАБЛИЦА: campaign_groups
-- Группы кампаний для мультиканальной аналитики
-- ==================================================

CREATE TABLE IF NOT EXISTS campaign_groups (
    id BIGSERIAL PRIMARY KEY,
    group_id VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_group_id ON campaign_groups(group_id);

-- ==================================================
-- 3. ТАБЛИЦА: campaigns
-- Данные фандрайзинговых кампаний
-- ==================================================

CREATE TABLE IF NOT EXISTS campaigns (
    id BIGSERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) UNIQUE NOT NULL,
    group_id VARCHAR(50),
    name VARCHAR(200) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    target_amount DECIMAL NOT NULL,
    collected_amount DECIMAL DEFAULT 0,
    ad_costs DECIMAL DEFAULT 0,
    labor_hours DECIMAL DEFAULT 0,
    hourly_rate DECIMAL DEFAULT 500,
    reach INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    donors_count INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (group_id) REFERENCES campaign_groups(group_id) ON DELETE SET NULL
);

-- Индексы для campaigns
CREATE INDEX IF NOT EXISTS idx_campaign_id ON campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_group ON campaigns(group_id);
CREATE INDEX IF NOT EXISTS idx_campaign_channel ON campaigns(channel);
CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaign_dates ON campaigns(start_date, end_date);

-- Триггер для campaigns
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================================================
-- 4. ТАБЛИЦА: collection_history
-- История сборов по кампаниям
-- ==================================================

CREATE TABLE IF NOT EXISTS collection_history (
    id BIGSERIAL PRIMARY KEY,
    history_id VARCHAR(50) UNIQUE NOT NULL,
    campaign_id VARCHAR(50) NOT NULL,
    update_date DATE NOT NULL,
    amount_added DECIMAL NOT NULL,
    total_after_update DECIMAL NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
);

-- Индексы для collection_history
CREATE INDEX IF NOT EXISTS idx_collection_campaign ON collection_history(campaign_id);
CREATE INDEX IF NOT EXISTS idx_collection_date ON collection_history(update_date);

-- ==================================================
-- 5. ТАБЛИЦА: program_financials
-- Финансовые данные программ
-- ==================================================

CREATE TABLE IF NOT EXISTS program_financials (
    id BIGSERIAL PRIMARY KEY,
    record_id VARCHAR(50) UNIQUE NOT NULL,
    program VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    income DECIMAL NOT NULL,
    expenses DECIMAL NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_program_period UNIQUE (program, year, month)
);

-- Индексы для program_financials
CREATE INDEX IF NOT EXISTS idx_financials_program ON program_financials(program);
CREATE INDEX IF NOT EXISTS idx_financials_period ON program_financials(year, month);
CREATE INDEX IF NOT EXISTS idx_financials_program_period ON program_financials(program, year, month);

-- Триггер для program_financials
CREATE TRIGGER update_program_financials_updated_at BEFORE UPDATE ON program_financials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==================================================

-- Для простоты использования в данном приложении,
-- разрешаем все операции для authenticated и anon ключей
-- В production рекомендуется настроить более строгие политики

-- kpi_history
ALTER TABLE kpi_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on kpi_history" ON kpi_history
    FOR ALL USING (true) WITH CHECK (true);

-- campaign_groups
ALTER TABLE campaign_groups ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on campaign_groups" ON campaign_groups
    FOR ALL USING (true) WITH CHECK (true);

-- campaigns
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on campaigns" ON campaigns
    FOR ALL USING (true) WITH CHECK (true);

-- collection_history
ALTER TABLE collection_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on collection_history" ON collection_history
    FOR ALL USING (true) WITH CHECK (true);

-- program_financials
ALTER TABLE program_financials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on program_financials" ON program_financials
    FOR ALL USING (true) WITH CHECK (true);

-- ==================================================
-- ПОЛЕЗНЫЕ ФУНКЦИИ
-- ==================================================

-- Функция для получения статистики по таблицам
CREATE OR REPLACE FUNCTION get_table_stats()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'kpi_history'::TEXT, COUNT(*)::BIGINT FROM kpi_history
    UNION ALL
    SELECT 'campaign_groups'::TEXT, COUNT(*)::BIGINT FROM campaign_groups
    UNION ALL
    SELECT 'campaigns'::TEXT, COUNT(*)::BIGINT FROM campaigns
    UNION ALL
    SELECT 'collection_history'::TEXT, COUNT(*)::BIGINT FROM collection_history
    UNION ALL
    SELECT 'program_financials'::TEXT, COUNT(*)::BIGINT FROM program_financials;
END;
$$ LANGUAGE plpgsql;

-- ==================================================
-- ЗАВЕРШЕНИЕ
-- ==================================================

-- Вывести статистику
SELECT * FROM get_table_stats();
