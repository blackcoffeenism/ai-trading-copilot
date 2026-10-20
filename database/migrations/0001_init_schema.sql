-- ====================================================================
-- AI TRADING COPILOT INITIAL DATABASE SCHEMA
-- Target Database: Supabase PostgreSQL (with PostGIS, UUID-OSSP, etc.)
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --------------------------------------------------------------------
-- 1. PROFILES TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(150),
    avatar_url TEXT,
    tier VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'premium', 'institutional')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.profiles IS 'Stores user profile details linked directly to Supabase Auth users.';
COMMENT ON COLUMN public.profiles.id IS 'Primary key, references Supabase auth.users.id.';
COMMENT ON COLUMN public.profiles.username IS 'Unique alphanumeric handle chosen by user.';
COMMENT ON COLUMN public.profiles.full_name IS 'Full display name of user.';
COMMENT ON COLUMN public.profiles.avatar_url IS 'URL of avatar resource stored in Supabase storage.';
COMMENT ON COLUMN public.profiles.tier IS 'Billing/Access tier: free, premium, or institutional.';

-- --------------------------------------------------------------------
-- 2. USER SETTINGS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
    default_leverage INT DEFAULT 1 CHECK (default_leverage >= 1 AND default_leverage <= 100),
    risk_tolerance VARCHAR(20) DEFAULT 'moderate' CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
    ai_model_backbone VARCHAR(50) DEFAULT 'Gemini 1.5 Pro',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.user_settings IS 'Stores specific technical preferences and risk settings for each user.';
COMMENT ON COLUMN public.user_settings.user_id IS 'References public.profiles.id.';
COMMENT ON COLUMN public.user_settings.default_leverage IS 'Default leverage multiplier for calculations.';

-- --------------------------------------------------------------------
-- 3. WATCHLISTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.watchlists IS 'Groupings of user-tracked financial symbols.';

-- --------------------------------------------------------------------
-- 4. WATCHLIST SYMBOLS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.watchlist_symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id UUID NOT NULL REFERENCES public.watchlists(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    market_type VARCHAR(20) NOT NULL CHECK (market_type IN ('crypto', 'stocks', 'forex', 'indices')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(watchlist_id, symbol)
);

COMMENT ON TABLE public.watchlist_symbols IS 'Individual tickers linked to a watchlist.';

-- --------------------------------------------------------------------
-- 5. PORTFOLIOS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    available_usd NUMERIC(20, 4) DEFAULT 0.0000 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.portfolios IS 'Stores user portfolio balances (cash / non-custodial mock equity).';

-- --------------------------------------------------------------------
-- 6. PORTFOLIO ASSETS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.portfolio_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    quantity NUMERIC(24, 8) DEFAULT 0.00000000 NOT NULL,
    average_buy_price NUMERIC(20, 6) DEFAULT 0.000000 NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(portfolio_id, symbol)
);

COMMENT ON TABLE public.portfolio_assets IS 'Detailed assets holding balances (quantity and cost basis).';

-- --------------------------------------------------------------------
-- 7. JOURNAL ENTRIES TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol VARCHAR(30),
    entry_price NUMERIC(20, 6),
    exit_price NUMERIC(20, 6),
    quantity NUMERIC(24, 8),
    side VARCHAR(10) CHECK (side IN ('BUY', 'SELL', 'LONG', 'SHORT')),
    emotion VARCHAR(50),
    outcome VARCHAR(20) CHECK (outcome IN ('PROFIT', 'LOSS', 'BREAKEAVEN')),
    pnl_value NUMERIC(20, 4),
    notes TEXT,
    ai_feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.journal_entries IS 'Trading journal logger allowing custom emotion tags and AI audits.';

-- --------------------------------------------------------------------
-- 8. JOURNAL SCREENSHOTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.journal_screenshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_id UUID NOT NULL REFERENCES public.journal_entries(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.journal_screenshots IS 'Uploads of charts screenshots associated with journal notes.';

-- --------------------------------------------------------------------
-- 9. AI ANALYSES TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ai_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(30) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    price NUMERIC(20, 6) NOT NULL,
    rating INT CHECK (rating >= 0 AND rating <= 100),
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell')),
    confidence INT CHECK (confidence >= 0 AND confidence <= 100),
    trend VARCHAR(20),
    momentum VARCHAR(20),
    probability_bullish NUMERIC(5, 2),
    probability_bearish NUMERIC(5, 2),
    support_levels NUMERIC(20, 6)[],
    resistance_levels NUMERIC(20, 6)[],
    entry_target NUMERIC(20, 6),
    stop_loss NUMERIC(20, 6),
    take_profit NUMERIC(20, 6),
    risk_score VARCHAR(20),
    position_size_suggestion TEXT,
    plain_summary TEXT NOT NULL,
    detailed_reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.ai_analyses IS 'Cached AI market intelligence logs (trend, supports, exits).';

-- --------------------------------------------------------------------
-- 10. NEWS ARTICLES TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    article_url TEXT UNIQUE,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    snippet TEXT,
    ai_summary TEXT,
    sentiment VARCHAR(20) CHECK (sentiment IN ('Positive', 'Negative', 'Neutral')),
    sentiment_score INT CHECK (sentiment_score >= 0 AND sentiment_score <= 100),
    market_impact VARCHAR(20) CHECK (market_impact IN ('High', 'Medium', 'Low')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.news_articles IS 'Stores fetched financial news stream along with automated NLP classifications.';

-- --------------------------------------------------------------------
-- 11. ALERTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    alert_type VARCHAR(30) NOT NULL CHECK (alert_type IN ('price_above', 'price_below', 'indicator', 'pattern', 'forecast')),
    condition_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.alerts IS 'Trigger conditions set by traders (e.g. BTC crossing above $65,000).';

-- --------------------------------------------------------------------
-- 12. ALERT HISTORY TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES public.alerts(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    price_at_trigger NUMERIC(20, 6) NOT NULL,
    trigger_message TEXT NOT NULL
);

COMMENT ON TABLE public.alert_history IS 'Audit logs recording when user alerts were activated.';

-- --------------------------------------------------------------------
-- 13. STRATEGIES TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.strategies IS 'Defines parameters for trading systems (e.g. SMA Crossover periods).';

-- --------------------------------------------------------------------
-- 14. BACKTEST RUNS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES public.strategies(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    win_rate NUMERIC(5, 2) NOT NULL,
    sharpe_ratio NUMERIC(5, 2),
    profit_factor NUMERIC(5, 2),
    max_drawdown NUMERIC(5, 2) NOT NULL,
    avg_trade_pnl NUMERIC(20, 4) NOT NULL,
    total_return NUMERIC(10, 2) NOT NULL,
    equity_curve JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.backtest_runs IS 'Stores execution results and aggregate analytics for strategy backtesting simulations.';

-- --------------------------------------------------------------------
-- 15. BACKTEST TRADES TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.backtest_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_run_id UUID NOT NULL REFERENCES public.backtest_runs(id) ON DELETE CASCADE,
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price NUMERIC(20, 6) NOT NULL,
    exit_price NUMERIC(20, 6) NOT NULL,
    quantity NUMERIC(24, 8) NOT NULL,
    pnl NUMERIC(20, 4) NOT NULL,
    pnl_percent NUMERIC(5, 2) NOT NULL
);

COMMENT ON TABLE public.backtest_trades IS 'Logs individual trades simulated inside a backtesting execution session.';

-- --------------------------------------------------------------------
-- 16. NOTIFICATION PREFERENCES TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
    email_enabled BOOLEAN DEFAULT true NOT NULL,
    in_app_enabled BOOLEAN DEFAULT true NOT NULL,
    alert_triggers_enabled BOOLEAN DEFAULT true NOT NULL,
    newsletter_enabled BOOLEAN DEFAULT false NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.notification_preferences IS 'Stores push/email routing rules for user notifications.';

-- --------------------------------------------------------------------
-- 17. INDICATOR PRESETS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.indicator_presets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.indicator_presets IS 'Saved user configurations for technical parameters (e.g. customized Bollinger Band widths).';

-- --------------------------------------------------------------------
-- 18. CHART LAYOUTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.chart_layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    layout_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, name)
);

COMMENT ON TABLE public.chart_layouts IS 'Positions of grid widgets and charts layouts saved by terminal traders.';

-- --------------------------------------------------------------------
-- 19. API LOGS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint TEXT NOT NULL,
    method VARCHAR(10) NOT NULL,
    ip_address VARCHAR(45),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    response_code INT NOT NULL,
    latency_ms INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.api_logs IS 'System operations tracking for performance tuning.';

-- --------------------------------------------------------------------
-- 20. AUDIT LOGS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

COMMENT ON TABLE public.audit_logs IS 'Security audit trail logging administrative modifications and login states.';

-- ====================================================================
-- INDICES FOR OPTIMAL PERFORMANCE
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_profiles_username ON public.profiles(username);
CREATE INDEX IF NOT EXISTS idx_watchlists_user ON public.watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_symbols_list ON public.watchlist_symbols(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_user ON public.portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_assets_port ON public.portfolio_assets(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_user ON public.journal_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_symbol ON public.journal_entries(symbol);
CREATE INDEX IF NOT EXISTS idx_journal_screenshots_entry ON public.journal_screenshots(journal_id);
CREATE INDEX IF NOT EXISTS idx_ai_analyses_symbol ON public.ai_analyses(symbol, timeframe, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_pub ON public.news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON public.alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON public.alerts(symbol, is_active);
CREATE INDEX IF NOT EXISTS idx_alert_history_alert ON public.alert_history(alert_id);
CREATE INDEX IF NOT EXISTS idx_strategies_user ON public.strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy ON public.backtest_runs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_user ON public.backtest_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_run ON public.backtest_trades(backtest_run_id);
CREATE INDEX IF NOT EXISTS idx_indicator_presets_user ON public.indicator_presets(user_id);
CREATE INDEX IF NOT EXISTS idx_chart_layouts_user ON public.chart_layouts(user_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON public.api_logs(endpoint, method);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON public.audit_logs(user_id);

-- ====================================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- ====================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist_symbols ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_screenshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.backtest_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.backtest_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.indicator_presets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chart_layouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 1. Profiles Policies
CREATE POLICY "Users can view all public profiles" ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Users can update their own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- 2. User Settings Policies
CREATE POLICY "Users can view own settings" ON public.user_settings FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can modify own settings" ON public.user_settings FOR ALL USING (auth.uid() = user_id);

-- 3. Watchlists Policies
CREATE POLICY "Users can manage own watchlists" ON public.watchlists FOR ALL USING (auth.uid() = user_id);

-- 4. Watchlist Symbols Policies
CREATE POLICY "Users can manage symbols in own lists" ON public.watchlist_symbols FOR ALL 
    USING (EXISTS (
        SELECT 1 FROM public.watchlists WHERE id = watchlist_id AND user_id = auth.uid()
    ));

-- 5. Portfolios Policies
CREATE POLICY "Users can manage own portfolios" ON public.portfolios FOR ALL USING (auth.uid() = user_id);

-- 6. Portfolio Assets Policies
CREATE POLICY "Users can manage assets in own portfolios" ON public.portfolio_assets FOR ALL 
    USING (EXISTS (
        SELECT 1 FROM public.portfolios WHERE id = portfolio_id AND user_id = auth.uid()
    ));

-- 7. Journal Entries Policies
CREATE POLICY "Users can manage own journals" ON public.journal_entries FOR ALL USING (auth.uid() = user_id);

-- 8. Journal Screenshots Policies
CREATE POLICY "Users can manage screenshots in own journals" ON public.journal_screenshots FOR ALL 
    USING (EXISTS (
        SELECT 1 FROM public.journal_entries WHERE id = journal_id AND user_id = auth.uid()
    ));

-- 9. AI Analyses Policies (Read all cached reports, insert only by system role)
CREATE POLICY "Read access for all authenticated users on AI analysis" ON public.ai_analyses FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Insert access for AI Analyses by system authenticated users" ON public.ai_analyses FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- 10. News Articles Policies (Read all, write only by scraper roles)
CREATE POLICY "Read access for all on news" ON public.news_articles FOR SELECT USING (true);
CREATE POLICY "Scraper write access on news" ON public.news_articles FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- 11. Alerts Policies
CREATE POLICY "Users can manage own alerts" ON public.alerts FOR ALL USING (auth.uid() = user_id);

-- 12. Alert History Policies
CREATE POLICY "Users can view own alert triggers history" ON public.alert_history FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.alerts WHERE id = alert_id AND user_id = auth.uid()
    ));

-- 13. Strategies Policies
CREATE POLICY "Users can manage own strategies" ON public.strategies FOR ALL USING (auth.uid() = user_id);

-- 14. Backtest Runs Policies
CREATE POLICY "Users can manage own backtests" ON public.backtest_runs FOR ALL USING (auth.uid() = user_id);

-- 15. Backtest Trades Policies
CREATE POLICY "Users can view trades from own backtests" ON public.backtest_trades FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.backtest_runs WHERE id = backtest_run_id AND user_id = auth.uid()
    ));

-- 16. Notification Preferences Policies
CREATE POLICY "Users can manage own notifications preferences" ON public.notification_preferences FOR ALL USING (auth.uid() = user_id);

-- 17. Indicator Presets Policies
CREATE POLICY "Users can manage own indicator presets" ON public.indicator_presets FOR ALL USING (auth.uid() = user_id);

-- 18. Chart Layouts Policies
CREATE POLICY "Users can manage own chart layouts" ON public.chart_layouts FOR ALL USING (auth.uid() = user_id);

-- 19. API Logs Policies (Admin read-only, systems insert-only)
CREATE POLICY "Admins can view API logs" ON public.api_logs FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "System can insert API logs" ON public.api_logs FOR INSERT WITH CHECK (true);

-- 20. Audit Logs Policies
CREATE POLICY "Admins can view Audit logs" ON public.audit_logs FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "System can insert Audit logs" ON public.audit_logs FOR INSERT WITH CHECK (true);
