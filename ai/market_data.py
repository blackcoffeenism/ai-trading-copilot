"""Market data, technical snapshot and global news helpers for the AI service.

- Price history comes from yfinance.
- News is pulled from Yahoo Finance plus Google News RSS editions for several
  regions (global coverage), plus macro/geopolitical queries that move markets.
- Headlines are scored with a finance sentiment lexicon (-1 bearish .. +1 bullish).
"""
import html
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------- symbols

_CRYPTO = {"BTC", "ETH", "SOL", "XRP", "ADA"}
_SPECIAL = {
    "JPY": "JPY=X", "Gold": "GC=F", "Crude Oil": "CL=F", "Silver": "SI=F",
    "S&P 500": "^GSPC", "Nasdaq 100": "^NDX", "Dow Jones": "^DJI",
    "Nvidia": "NVDA", "JFC": "JFC.PS", "ALI": "ALI.PS", "BDO": "BDO.PS",
    "SM": "SM.PS", "TEL": "TEL.PS",
}
_FX = {"EUR", "GBP", "AUD"}

# Friendly names used for news search queries
_NEWS_NAMES = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "XRP": "XRP Ripple",
    "ADA": "Cardano", "Nvidia": "Nvidia", "AAPL": "Apple", "TSLA": "Tesla",
    "MSFT": "Microsoft", "AMZN": "Amazon", "GOOGL": "Google Alphabet",
    "EUR": "Euro dollar EURUSD", "GBP": "British pound GBPUSD",
    "JPY": "Japanese yen USDJPY", "AUD": "Australian dollar AUDUSD",
    "Gold": "gold price", "Crude Oil": "crude oil price", "Silver": "silver price",
    "S&P 500": "S&P 500", "Nasdaq 100": "Nasdaq", "Dow Jones": "Dow Jones",
    "JFC": "Jollibee Foods", "ALI": "Ayala Land", "BDO": "BDO Unibank",
    "SM": "SM Investments", "TEL": "PLDT",
}

# Macro / geopolitical topics that move stocks worldwide
_MACRO_QUERIES = [
    "stock market global economy",
    "Federal Reserve interest rates inflation",
    "oil prices OPEC geopolitical",
    "China economy trade tariffs",
]

# Google News editions: (hl, gl, ceid)
_EDITIONS = [
    ("en-US", "US", "US:en"),
    ("en-GB", "GB", "GB:en"),
    ("en-IN", "IN", "IN:en"),
    ("en-AU", "AU", "AU:en"),
    ("en-SG", "SG", "SG:en"),
    ("en-PH", "PH", "PH:en"),
]


def resolve_symbol(symbol: str) -> str:
    if symbol in _SPECIAL:
        return _SPECIAL[symbol]
    if symbol in _CRYPTO:
        return f"{symbol}-USD"
    if symbol in _FX:
        return f"{symbol}USD=X"
    return symbol


def timeframe_params(timeframe: str) -> tuple:
    if timeframe == "1H":
        return "7d", "1h"
    if timeframe == "4H":
        return "30d", "1h"
    if timeframe == "1W":
        return "2y", "1wk"
    return "1y", "1d"


# ---------------------------------------------------------------- technicals

@dataclass
class Snapshot:
    price: float
    rsi: float
    macd_hist: float
    trend: int  # 1 = uptrend (EMA20 > EMA50), -1 = downtrend
    ema20: float
    ema50: float
    support: float
    resistance: float
    change_pct: float  # % change over the last 20 bars


_UA = {"User-Agent": "Mozilla/5.0"}


def fetch_history_df(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """OHLC history straight from Yahoo's chart API (DataFrame indexed by UTC time)."""
    period, interval = timeframe_params(timeframe)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote_plus(resolve_symbol(symbol))}"
    try:
        r = requests.get(url, params={"range": period, "interval": interval}, headers=_UA, timeout=10)
        r.raise_for_status()
        res = r.json()["chart"]["result"][0]
        q = res["indicators"]["quote"][0]
        df = pd.DataFrame(
            {"Open": q["open"], "High": q["high"], "Low": q["low"], "Close": q["close"]},
            index=pd.to_datetime(res["timestamp"], unit="s", utc=True),
        ).dropna()
        return df if not df.empty else None
    except Exception as e:
        print(f"History fetch failed for {symbol}: {e}")
        return None


def get_snapshot(symbol: str, timeframe: str) -> Optional[Snapshot]:
    """Compute real indicators from recent price history."""
    try:
        df = fetch_history_df(symbol, timeframe)
        if df is None or len(df) < 30:
            return None
        close = pd.Series(df["Close"]).astype(float)
        high = pd.Series(df["High"]).astype(float)
        low = pd.Series(df["Low"]).astype(float)

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = pd.Series(100 - (100 / (1 + gain / (loss + 1e-9))))

        macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        hist = macd - macd.ewm(span=9, adjust=False).mean()
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()

        last20 = slice(-20, None)
        base = float(close.iloc[-20]) if len(close) >= 20 else float(close.iloc[0])
        return Snapshot(
            price=float(close.iloc[-1]),
            rsi=float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0,
            macd_hist=float(hist.iloc[-1]),
            trend=1 if ema20.iloc[-1] > ema50.iloc[-1] else -1,
            ema20=float(ema20.iloc[-1]),
            ema50=float(ema50.iloc[-1]),
            support=float(low.iloc[last20].min()),
            resistance=float(high.iloc[last20].max()),
            change_pct=(float(close.iloc[-1]) / base - 1) * 100 if base else 0.0,
        )
    except Exception as e:
        print(f"Snapshot failed for {symbol}: {e}")
        return None


# ---------------------------------------------------------------- sentiment

_POS = {
    "surge", "surges", "soar", "soars", "rally", "rallies", "gain", "gains", "jump", "jumps",
    "beat", "beats", "record", "growth", "profit", "profits", "upgrade", "upgrades", "bullish",
    "strong", "outperform", "boost", "boosts", "rebound", "recovery", "approval", "approved",
    "expands", "expansion", "partnership", "deal", "buyback", "dividend", "optimism", "rise",
    "rises", "climb", "climbs", "high", "breakthrough", "ceasefire", "cut rates", "rate cut",
}
_NEG = {
    "plunge", "plunges", "crash", "crashes", "fall", "falls", "drop", "drops", "slump", "slumps",
    "miss", "misses", "loss", "losses", "downgrade", "downgrades", "bearish", "weak", "lawsuit",
    "probe", "investigation", "fraud", "recall", "layoffs", "layoff", "cut", "cuts", "decline",
    "declines", "fear", "fears", "recession", "inflation", "tariff", "tariffs", "sanctions",
    "war", "attack", "default", "bankruptcy", "ban", "bans", "hack", "selloff", "sell-off",
    "warning", "warns", "risk", "crisis", "rate hike", "tumble", "tumbles",
}


def score_text(text: str) -> float:
    t = text.lower()
    words = re.findall(r"[a-z\-]+", t)
    pos = sum(1 for w in words if w in _POS) + sum(1 for p in _POS if " " in p and p in t)
    neg = sum(1 for w in words if w in _NEG) + sum(1 for p in _NEG if " " in p and p in t)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


# ---------------------------------------------------------------- news

_cache: Dict[str, Any] = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 300  # seconds


def _parse_date(raw: str) -> Optional[datetime]:
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _google_news(query: str, edition: tuple, tag_name: str) -> List[Dict[str, Any]]:
    hl, gl, ceid = edition
    url = (
        f"https://news.google.com/rss/search?q={quote_plus(query + ' when:3d')}"
        f"&hl={hl}&gl={gl}&ceid={ceid}"
    )
    out: List[Dict[str, Any]] = []
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        text = r.text
        for block in re.findall(r"<item>(.*?)</item>", text, flags=re.S):
            def tag(name: str) -> str:
                m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", block, flags=re.S)
                if not m:
                    return ""
                v = re.sub(r"^<!\[CDATA\[|\]\]>$", "", m.group(1).strip())
                return html.unescape(v).strip()
            title = tag("title")
            if not title:
                continue
            published = _parse_date(tag("pubDate"))
            out.append({
                "title": title,
                "source": tag("source") or "Google News",
                "url": tag("link"),
                "published": published.isoformat() if published else "",
                "region": gl,
                "scope": tag_name,
            })
            if len(out) >= 8:
                break
    except Exception as e:
        print(f"News fetch failed ({query!r}, {gl}): {e}")
    return out


def _yahoo_news(symbol: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": resolve_symbol(symbol), "newsCount": 10, "quotesCount": 0},
            headers=_UA, timeout=8,
        )
        r.raise_for_status()
        for n in r.json().get("news", [])[:10]:
            title = n.get("title")
            if not title:
                continue
            ts = n.get("providerPublishTime")
            out.append({
                "title": title,
                "source": n.get("publisher", "Yahoo Finance"),
                "url": n.get("link", ""),
                "published": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else "",
                "region": "GLOBAL",
                "scope": "company",
            })
    except Exception as e:
        print(f"Yahoo news failed for {symbol}: {e}")
    return out


def fetch_news(symbol: str, limit: int = 10) -> Dict[str, Any]:
    """Fetch worldwide news affecting `symbol` and score it.

    Returns {"articles": [...], "sentiment": float(-1..1), "count": int}.
    """
    key = f"news:{symbol}"
    with _cache_lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < _CACHE_TTL:
            return hit[1]

    name = _NEWS_NAMES.get(symbol, symbol)
    jobs = [(f"{name} stock" if symbol not in _CRYPTO else name, ed, "company") for ed in _EDITIONS]
    jobs += [(q, _EDITIONS[0], "macro") for q in _MACRO_QUERIES]
    jobs += [(_MACRO_QUERIES[0], _EDITIONS[1], "macro"), (_MACRO_QUERIES[0], _EDITIONS[2], "macro")]

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_google_news, q, ed, tag) for q, ed, tag in jobs]
        futures.append(pool.submit(_yahoo_news, symbol))  # type: ignore[arg-type]
        for f in futures:
            try:
                results.extend(f.result(timeout=10))
            except Exception:
                pass

    # De-duplicate by normalised title, drop stale items (>7 days)
    now = datetime.now(timezone.utc)
    seen = set()
    articles: List[Dict[str, Any]] = []
    for a in results:
        k = re.sub(r"\W+", " ", a["title"].lower())[:80]
        if k in seen:
            continue
        seen.add(k)
        if a["published"]:
            try:
                age = (now - datetime.fromisoformat(a["published"])).total_seconds()
                if age > 7 * 86400:
                    continue
            except Exception:
                pass
        a["sentiment"] = round(score_text(a["title"]), 2)
        articles.append(a)

    # Company news first, then macro; newest first within each group
    articles.sort(key=lambda a: (a["scope"] != "company", -(_ts(a["published"]))))

    # Weighted sentiment: company news counts double vs macro
    weights, total = 0.0, 0.0
    for a in articles:
        w = 2.0 if a["scope"] == "company" else 1.0
        total += a["sentiment"] * w
        weights += w
    sentiment = total / weights if weights else 0.0

    payload = {"articles": articles[:limit], "sentiment": round(sentiment, 3), "count": len(articles)}
    with _cache_lock:
        _cache[key] = (time.time(), payload)
    return payload


def _ts(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0
