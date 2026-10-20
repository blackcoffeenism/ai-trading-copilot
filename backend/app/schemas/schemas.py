from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

# --- Profile & User Settings ---
class ProfileBase(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    tier: Optional[str] = "free"

class ProfileRead(ProfileBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserSettingBase(BaseModel):
    default_leverage: int = Field(default=1, ge=1, le=100)
    risk_tolerance: str = "moderate"
    ai_model_backbone: str = "Gemini 1.5 Pro"

class UserSettingRead(UserSettingBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Watchlists ---
class WatchlistSymbolBase(BaseModel):
    symbol: str
    market_type: str

class WatchlistSymbolCreate(WatchlistSymbolBase):
    pass

class WatchlistSymbolRead(WatchlistSymbolBase):
    id: str
    watchlist_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class WatchlistBase(BaseModel):
    name: str
    is_default: bool = False

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistRead(WatchlistBase):
    id: str
    user_id: str
    symbols: List[WatchlistSymbolRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Portfolios ---
class PortfolioAssetBase(BaseModel):
    symbol: str
    quantity: Decimal
    average_buy_price: Decimal

class PortfolioAssetRead(PortfolioAssetBase):
    id: str
    portfolio_id: str
    updated_at: datetime

    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    name: str
    available_usd: Decimal = Decimal("0.00")

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioRead(PortfolioBase):
    id: str
    user_id: str
    assets: List[PortfolioAssetRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Trading Journal ---
class JournalEntryBase(BaseModel):
    symbol: Optional[str] = None
    entry_price: Optional[Decimal] = None
    exit_price: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    side: Optional[str] = None
    emotion: Optional[str] = None
    outcome: Optional[str] = None
    pnl_value: Optional[Decimal] = None
    notes: Optional[str] = None

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalScreenshotRead(BaseModel):
    id: str
    journal_id: str
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class JournalEntryRead(JournalEntryBase):
    id: str
    user_id: str
    ai_feedback: Optional[str] = None
    screenshots: List[JournalScreenshotRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- AI Analyses ---
class AIAnalysisRead(BaseModel):
    id: str
    symbol: str
    timeframe: str
    price: Decimal
    rating: int
    signal_type: str
    confidence: int
    trend: Optional[str] = None
    momentum: Optional[str] = None
    probability_bullish: Optional[float] = None
    probability_bearish: Optional[float] = None
    support_levels: Optional[List[Decimal]] = None
    resistance_levels: Optional[List[Decimal]] = None
    entry_target: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    risk_score: Optional[str] = None
    position_size_suggestion: Optional[str] = None
    plain_summary: str
    detailed_reasoning: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- News Articles ---
class NewsArticleRead(BaseModel):
    id: str
    title: str
    source: str
    article_url: Optional[str] = None
    published_at: datetime
    snippet: Optional[str] = None
    ai_summary: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[int] = None
    market_impact: Optional[str] = None

    class Config:
        from_attributes = True

# --- Alerts ---
class AlertBase(BaseModel):
    symbol: str
    alert_type: str
    condition_value: str
    is_active: bool = True

class AlertCreate(AlertBase):
    pass

class AlertHistoryRead(BaseModel):
    id: str
    alert_id: str
    triggered_at: datetime
    price_at_trigger: Decimal
    trigger_message: str

    class Config:
        from_attributes = True

class AlertRead(AlertBase):
    id: str
    user_id: str
    history: List[AlertHistoryRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Backtesting & Strategies ---
class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}

class StrategyCreate(StrategyBase):
    pass

class StrategyRead(StrategyBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BacktestTradeRead(BaseModel):
    id: str
    backtest_run_id: str
    entry_time: datetime
    exit_time: datetime
    side: str
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    pnl: Decimal
    pnl_percent: float

    class Config:
        from_attributes = True

class BacktestRunRead(BaseModel):
    id: str
    strategy_id: Optional[str] = None
    user_id: str
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    win_rate: float
    sharpe_ratio: Optional[float] = None
    profit_factor: Optional[float] = None
    max_drawdown: float
    avg_trade_pnl: Decimal
    total_return: float
    equity_curve: List[Dict[str, Any]] = []
    trades: List[BacktestTradeRead] = []
    created_at: datetime

    class Config:
        from_attributes = True
