from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
import datetime

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, CurrentUser
from backend.app.models.models import (
    Profile, Watchlist, WatchlistSymbol, Portfolio, PortfolioAsset,
    JournalEntry, NewsArticle, Alert, Strategy, BacktestRun,
    BacktestTrade, UserSetting, AIAnalysis
)
from backend.app.schemas.schemas import (
    WatchlistRead, WatchlistCreate, WatchlistSymbolCreate, WatchlistSymbolRead,
    PortfolioRead, JournalEntryRead, JournalEntryCreate,
    AlertRead, AlertCreate, StrategyRead, StrategyCreate, BacktestRunRead,
    AIAnalysisRead, NewsArticleRead
)

router = APIRouter()

# ==========================================
# 1. PROFILE & SETTINGS ENDPOINTS
# ==========================================
@router.get("/profile", response_model=Dict[str, Any])
def get_user_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()
    if not profile:
        # Auto-create profile in DB if user exists in auth (convenience for Supabase)
        profile = Profile(id=current_user.id, username=f"user_{current_user.id[:8]}", tier="free")
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
    # Check settings
    settings = db.query(UserSetting).filter(UserSetting.user_id == current_user.id).first()
    if not settings:
        settings = UserSetting(user_id=current_user.id, default_leverage=1, risk_tolerance="moderate")
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
    return {
        "id": profile.id,
        "username": profile.username,
        "full_name": profile.full_name,
        "tier": profile.tier,
        "settings": {
            "default_leverage": settings.default_leverage,
            "risk_tolerance": settings.risk_tolerance,
            "ai_model": settings.ai_model_backbone
        }
    }

# ==========================================
# 2. WATCHLIST ENDPOINTS
# ==========================================
@router.get("/watchlist", response_model=List[WatchlistRead])
def get_watchlists(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()

@router.post("/watchlist", response_model=WatchlistRead)
def create_watchlist(
    data: WatchlistCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    watchlist = Watchlist(user_id=current_user.id, name=data.name, is_default=data.is_default)
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    return watchlist

@router.post("/watchlist/{watchlist_id}/symbols", response_model=WatchlistSymbolRead)
def add_watchlist_symbol(
    watchlist_id: str,
    data: WatchlistSymbolCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
        
    # Check if duplicate
    dup = db.query(WatchlistSymbol).filter(
        WatchlistSymbol.watchlist_id == watchlist_id,
        WatchlistSymbol.symbol == data.symbol
    ).first()
    if dup:
        raise HTTPException(status_code=400, detail="Symbol already exists in this watchlist")
        
    ws = WatchlistSymbol(watchlist_id=watchlist_id, symbol=data.symbol.upper(), market_type=data.market_type)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws

@router.delete("/watchlist/{watchlist_id}/symbols/{symbol}", status_code=204)
def delete_watchlist_symbol(
    watchlist_id: str,
    symbol: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
        
    ws = db.query(WatchlistSymbol).filter(
        WatchlistSymbol.watchlist_id == watchlist_id,
        WatchlistSymbol.symbol == symbol.upper()
    ).first()
    
    if not ws:
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")
        
    db.delete(ws)
    db.commit()

# ==========================================
# 3. PORTFOLIO & ORDERS ENDPOINTS
# ==========================================
@router.get("/portfolio", response_model=List[PortfolioRead])
def get_portfolios(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    if not portfolios:
        # Create default mock portfolio for user
        default_port = Portfolio(user_id=current_user.id, name="Default Mock Portfolio", available_usd=Decimal("50000.00"))
        db.add(default_port)
        db.commit()
        db.refresh(default_port)
        portfolios = [default_port]
    return portfolios

@router.post("/portfolio/{portfolio_id}/order")
def execute_portfolio_order(
    portfolio_id: str,
    symbol: str,
    side: str,      # BUY or SELL
    order_type: str, # LIMIT or MARKET
    quantity: float,
    price: float,
    leverage: int = 1,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes a mock trade order, updating cash and assets balances."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    qty = Decimal(str(quantity))
    prc = Decimal(str(price))
    cost = qty * prc
    margin = cost / Decimal(str(leverage))
    
    if side.upper() == "BUY":
        if margin > portfolio.available_usd:
            raise HTTPException(status_code=400, detail="Insufficient available margin funds")
            
        portfolio.available_usd -= margin
        
        # Upsert portfolio asset
        asset = db.query(PortfolioAsset).filter(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.symbol == symbol.upper()
        ).first()
        if not asset:
            asset = PortfolioAsset(portfolio_id=portfolio_id, symbol=symbol.upper(), quantity=Decimal("0"), average_buy_price=Decimal("0"))
            db.add(asset)
            
        old_cost = asset.quantity * asset.average_buy_price
        asset.quantity += qty
        asset.average_buy_price = (old_cost + cost) / asset.quantity
        
    elif side.upper() == "SELL":
        asset = db.query(PortfolioAsset).filter(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.symbol == symbol.upper()
        ).first()
        if not asset or asset.quantity < qty:
            raise HTTPException(status_code=400, detail=f"Insufficient {symbol} holdings to sell")
            
        asset.quantity -= qty
        portfolio.available_usd += margin  # refund margin cost
        
        if asset.quantity <= Decimal("0.0001"):
            db.delete(asset)
            
    else:
        raise HTTPException(status_code=400, detail="Invalid order side")
        
    db.commit()
    db.refresh(portfolio)
    return {"status": "success", "available_usd": float(portfolio.available_usd)}

# ==========================================
# 4. JOURNAL ENDPOINTS
# ==========================================
@router.get("/journal", response_model=List[JournalEntryRead])
def get_journal_entries(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(JournalEntry).filter(JournalEntry.user_id == current_user.id).order_by(JournalEntry.created_at.desc()).all()

@router.post("/journal", response_model=JournalEntryRead)
def create_journal_entry(
    data: JournalEntryCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Perform a mock AI feedback review of the journal entry
    feedback = f"AI FEEDBACK: Entry logged successfully. Trade on {data.symbol} ({data.side}) showed "
    if data.notes and len(data.notes) > 10:
        feedback += f"proper emotional grounding ({data.emotion}). Focus on executing strictly based on your SMA strategy."
    else:
        feedback += "good execution parameters. Please write detailed journal notes for deeper cognitive analysis."

    entry = JournalEntry(
        user_id=current_user.id,
        symbol=data.symbol,
        entry_price=data.entry_price,
        exit_price=data.exit_price,
        quantity=data.quantity,
        side=data.side,
        emotion=data.emotion,
        outcome=data.outcome,
        pnl_value=data.pnl_value,
        notes=data.notes,
        ai_feedback=feedback
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

# ==========================================
# 5. ALERTS ENDPOINTS
# ==========================================
@router.get("/alerts", response_model=List[AlertRead])
def get_alerts(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Alert).filter(Alert.user_id == current_user.id).all()

@router.post("/alerts", response_model=AlertRead)
def create_alert(
    data: AlertCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = Alert(
        user_id=current_user.id,
        symbol=data.symbol.upper(),
        alert_type=data.alert_type,
        condition_value=data.condition_value,
        is_active=data.is_active
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

@router.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(
    alert_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()

# ==========================================
# 6. STRATEGIES & BACKTESTING ENDPOINTS
# ==========================================
@router.get("/strategy", response_model=List[StrategyRead])
def get_strategies(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Strategy).filter(Strategy.user_id == current_user.id).all()

@router.post("/strategy", response_model=StrategyRead)
def create_strategy(
    data: StrategyCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    strategy = Strategy(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        parameters=data.parameters
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy

@router.post("/backtest/run", response_model=BacktestRunRead)
def run_strategy_backtest(
    strategy_id: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triggers backtest simulation and logs metrics."""
    # Generate some mock backtesting results representing a professional analysis
    win_rate = 62.4
    sharpe = 1.82
    profit_factor = 1.45
    drawdown = 8.5
    total_return = 24.5
    
    # Calculate mock equity curve
    equity_curve = []
    base_equity = 10000.00
    current_time = datetime.datetime.now() - datetime.timedelta(days=30)
    for i in range(30):
        base_equity += base_equity * (0.01 + (i % 3 == 0 and -0.02 or 0.025))
        equity_curve.append({
            "time": (current_time + datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
            "value": base_equity
        })
        
    run = BacktestRun(
        strategy_id=strategy_id,
        user_id=current_user.id,
        symbol=symbol.upper(),
        timeframe=timeframe,
        start_date=datetime.datetime.strptime(start_date, "%Y-%m-%d"),
        end_date=datetime.datetime.strptime(end_date, "%Y-%m-%d"),
        win_rate=win_rate,
        sharpe_ratio=sharpe,
        profit_factor=profit_factor,
        max_drawdown=drawdown,
        avg_trade_pnl=Decimal("124.50"),
        total_return=total_return,
        equity_curve=equity_curve
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Generate mock trades
    for i in range(5):
        trade = BacktestTrade(
            backtest_run_id=run.id,
            entry_time=datetime.datetime.now() - datetime.timedelta(days=5 - i),
            exit_time=datetime.datetime.now() - datetime.timedelta(days=5 - i, hours=12),
            side="BUY" if i % 2 == 0 else "SELL",
            entry_price=Decimal("62000.00") + (i * 500),
            exit_price=Decimal("63000.00") + (i * 450),
            quantity=Decimal("0.1"),
            pnl=Decimal("100.00") if i % 2 == 0 else Decimal("-50.00"),
            pnl_percent=1.5 if i % 2 == 0 else -0.75
        )
        db.add(trade)
    db.commit()
    db.refresh(run)
    return run

# ==========================================
# 7. AI ANALYSIS & NEWS ENDPOINTS
# ==========================================
@router.get("/news", response_model=List[NewsArticleRead])
def get_news_articles(db: Session = Depends(get_db)):
    articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(10).all()
    if not articles:
        # Prepopulate with mock articles from configuration
        mock_news = [
            {"title": "Federal Reserve Signals Potential Rate Cut in Upcoming Meeting", "source": "Bloomberg", "snippet": "Fed chairman hints inflation indicators are cooling, raising expectations of rate relief next month.", "sentiment": "Positive", "sentiment_score": 88, "market_impact": "High"},
            {"title": "SEC Approves In-Kind Creation Options for Cryptic Index Products", "source": "Reuters", "snippet": "New regulatory approvals clear path for major institutional capital deployment into derivative holdings.", "sentiment": "Positive", "sentiment_score": 94, "market_impact": "High"},
            {"title": "MicroStrategy Acquires Additional 12,000 BTC for $780 Million", "source": "CoinDesk", "snippet": "Company continues treasury reserves consolidation, bringing total asset holding value beyond $14B.", "sentiment": "Positive", "sentiment_score": 91, "market_impact": "Medium"},
            {"title": "Tech Giants Retrace as Valuation Multiples Face Growth Headwinds", "source": "Wall Street Journal", "snippet": "Earnings revisions signal moderate slowdown in AI capital investments for tech conglomerates.", "sentiment": "Negative", "sentiment_score": 72, "market_impact": "Medium"}
        ]
        for mn in mock_news:
            art = NewsArticle(
                title=mn["title"],
                source=mn["source"],
                snippet=mn["snippet"],
                published_at=datetime.datetime.now() - datetime.timedelta(hours=2),
                sentiment=mn["sentiment"],
                sentiment_score=mn["sentiment_score"],
                market_impact=mn["market_impact"]
            )
            db.add(art)
        db.commit()
        articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(10).all()
    return articles

@router.get("/analysis/{symbol}/{timeframe}", response_model=AIAnalysisRead)
def get_ai_analysis(
    symbol: str,
    timeframe: str,
    db: Session = Depends(get_db)
):
    analysis = db.query(AIAnalysis).filter(
        AIAnalysis.symbol == symbol.upper(),
        AIAnalysis.timeframe == timeframe
    ).order_by(AIAnalysis.created_at.desc()).first()
    
    if not analysis:
        # Generate default analysis record for convenience
        analysis = AIAnalysis(
            symbol=symbol.upper(),
            timeframe=timeframe,
            price=Decimal("64230.50"),
            rating=88,
            signal_type="Strong Buy",
            confidence=92,
            trend="Bullish",
            momentum="Strong Upward",
            probability_bullish=92.00,
            probability_bearish=8.00,
            support_levels=[Decimal("62100.00"), Decimal("60500.00")],
            resistance_levels=[Decimal("65800.00"), Decimal("67200.00")],
            entry_target=Decimal("63800.00"),
            stop_loss=Decimal("61500.00"),
            take_profit=Decimal("67500.00"),
            risk_score="Medium",
            position_size_suggestion="2.5% of total capital",
            plain_summary=f"Indicators for {symbol.upper()} suggest strong upward support and bullish consolidation triggers. Recommended entry is around support.",
            detailed_reasoning=f"Technical oscillators are flashing bullish cues on the {timeframe} timeframe. RSI index at 62 indicates healthy momentum.",
            created_at=datetime.datetime.now()
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
    return analysis
