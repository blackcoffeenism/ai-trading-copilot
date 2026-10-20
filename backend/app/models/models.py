import uuid
from decimal import Decimal
from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, ForeignKey, Text, JSON, ARRAY, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.app.core.database import Base

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(150))
    avatar_url = Column(Text)
    tier = Column(String(20), default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    settings = relationship("UserSetting", back_populates="user", uselist=False)
    watchlists = relationship("Watchlist", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    journal_entries = relationship("JournalEntry", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    backtest_runs = relationship("BacktestRun", back_populates="user")
    notification_prefs = relationship("NotificationPreference", back_populates="user", uselist=False)
    indicator_presets = relationship("IndicatorPreset", back_populates="user")
    chart_layouts = relationship("ChartLayout", back_populates="user")

class UserSetting(Base):
    __tablename__ = "user_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True)
    default_leverage = Column(Integer, default=1)
    risk_tolerance = Column(String(20), default="moderate")
    ai_model_backbone = Column(String(50), default="Gemini 1.5 Pro")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="settings")

class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="watchlists")
    symbols = relationship("WatchlistSymbol", back_populates="watchlist", cascade="all, delete-orphan")

class WatchlistSymbol(Base):
    __tablename__ = "watchlist_symbols"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    watchlist_id = Column(String(36), ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False)
    market_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    watchlist = relationship("Watchlist", back_populates="symbols")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    available_usd: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0.0000, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="portfolios")
    assets = relationship("PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan")

class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String(36), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0.00000000, nullable=False)
    average_buy_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0.000000, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    portfolio = relationship("Portfolio", back_populates="assets")

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30))
    entry_price = Column(Numeric(20, 6))
    exit_price = Column(Numeric(20, 6))
    quantity = Column(Numeric(24, 8))
    side = Column(String(10))
    emotion = Column(String(50))
    outcome = Column(String(20))
    pnl_value = Column(Numeric(20, 4))
    notes = Column(Text)
    ai_feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="journal_entries")
    screenshots = relationship("JournalScreenshot", back_populates="journal", cascade="all, delete-orphan")

class JournalScreenshot(Base):
    __tablename__ = "journal_screenshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_id = Column(String(36), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    journal = relationship("JournalEntry", back_populates="screenshots")

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(30), nullable=False)
    timeframe = Column(String(10), nullable=False)
    price = Column(Numeric(20, 6), nullable=False)
    rating = Column(Integer)
    signal_type = Column(String(20), nullable=False)
    confidence = Column(Integer)
    trend = Column(String(20))
    momentum = Column(String(20))
    probability_bullish = Column(Numeric(5, 2))
    probability_bearish = Column(Numeric(5, 2))
    support_levels = Column(ARRAY(Numeric(20, 6)))
    resistance_levels = Column(ARRAY(Numeric(20, 6)))
    entry_target = Column(Numeric(20, 6))
    stop_loss = Column(Numeric(20, 6))
    take_profit = Column(Numeric(20, 6))
    risk_score = Column(String(20))
    position_size_suggestion = Column(Text)
    plain_summary = Column(Text, nullable=False)
    detailed_reasoning = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    article_url = Column(Text, unique=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    snippet = Column(Text)
    ai_summary = Column(Text)
    sentiment = Column(String(20))
    sentiment_score = Column(Integer)
    market_impact = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False)
    alert_type = Column(String(30), nullable=False)
    condition_value = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")

class AlertHistory(Base):
    __tablename__ = "alert_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    price_at_trigger = Column(Numeric(20, 6), nullable=False)
    trigger_message = Column(Text, nullable=False)
    
    alert = relationship("Alert", back_populates="history")

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parameters = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="strategies")
    backtest_runs = relationship("BacktestRun", back_populates="strategy")

class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="SET NULL"))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    win_rate = Column(Numeric(5, 2), nullable=False)
    sharpe_ratio = Column(Numeric(5, 2))
    profit_factor = Column(Numeric(5, 2))
    max_drawdown = Column(Numeric(5, 2), nullable=False)
    avg_trade_pnl = Column(Numeric(20, 4), nullable=False)
    total_return = Column(Numeric(10, 2), nullable=False)
    equity_curve = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="backtest_runs")
    strategy = relationship("Strategy", back_populates="backtest_runs")
    trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")

class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backtest_run_id = Column(String(36), ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=False)
    side = Column(String(10), nullable=False)
    entry_price = Column(Numeric(20, 6), nullable=False)
    exit_price = Column(Numeric(20, 6), nullable=False)
    quantity = Column(Numeric(24, 8), nullable=False)
    pnl = Column(Numeric(20, 4), nullable=False)
    pnl_percent = Column(Numeric(5, 2), nullable=False)
    
    backtest_run = relationship("BacktestRun", back_populates="trades")

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    alert_triggers_enabled = Column(Boolean, default=True, nullable=False)
    newsletter_enabled = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="notification_prefs")

class IndicatorPreset(Base):
    __tablename__ = "indicator_presets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    config = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="indicator_presets")

class ChartLayout(Base):
    __tablename__ = "chart_layouts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    layout_config = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("Profile", back_populates="chart_layouts")

class ApiLog(Base):
    __tablename__ = "api_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(Text, nullable=False)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(45))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"))
    response_code = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"))
    action_type = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
