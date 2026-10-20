import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd

try:
    from market_data import get_snapshot, fetch_news, fetch_history_df
except ImportError:  # when imported as package (ai.app)
    from .market_data import get_snapshot, fetch_news, fetch_history_df

# Try loading huggingface transformers
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    QWEN_AVAILABLE = True
except ImportError:
    QWEN_AVAILABLE = False

import threading
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load Qwen model in a background thread so server starts up instantly
    threading.Thread(target=load_qwen_model, daemon=True).start()
    yield

app = FastAPI(title="Qwen AI Trading Copilot Analysis Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AI Trading Copilot Analysis Engine",
        "endpoints": ["/analyze", "/history", "/health"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

class AnalysisRequest(BaseModel):
    symbol: str
    timeframe: str
    price: float
    indicators: Dict[str, Any]
    patterns: List[Dict[str, Any]]
    question: str = ""

class AnalysisResponse(BaseModel):
    rating: int
    signal_type: str
    confidence: int
    trend: str
    momentum: str
    probability_bullish: float
    probability_bearish: float
    support_levels: List[float]
    resistance_levels: List[float]
    entry_target: float
    stop_loss: float
    take_profit: float
    risk_score: str
    position_size_suggestion: str
    plain_summary: str
    detailed_reasoning: str
    method: str
    price: float = 0.0
    news: List[Dict[str, Any]] = []
    news_sentiment: float = 0.0
    news_count: int = 0

# Model variables
tokenizer = None
model = None

def load_qwen_model():
    global tokenizer, model
    if QWEN_AVAILABLE:
        try:
            print("Loading Qwen 2.5 Instruct model...")
            model_name = "Qwen/Qwen2.5-1.5B-Instruct"  # Using smaller variant in dev environment for low VRAM
            tokenizer = AutoTokenizer.from_pretrained(model_name)  # pyright: ignore[reportPossiblyUnboundVariable]
            model = AutoModelForCausalLM.from_pretrained(  # pyright: ignore[reportPossiblyUnboundVariable]
                model_name,
                device_map="cpu",  # CPU fallback
                torch_dtype=torch.float32  # pyright: ignore[reportPossiblyUnboundVariable]
            )
            print("Qwen model loaded successfully.")
        except Exception as e:
            print(f"Failed to load Qwen model: {str(e)}. Using cognitive fallback generator.")
            model = None
    else:
        print("Huggingface transformers package not installed. Running in cognitive heuristic mode.")

@app.post("/analyze", response_model=AnalysisResponse)
def run_analysis(req: AnalysisRequest):
    # 1. Real chart data (falls back to client-supplied indicators if unavailable)
    snap = get_snapshot(req.symbol, req.timeframe)
    if snap:
        rsi, macd_hist, supertrend_dir = snap.rsi, snap.macd_hist, snap.trend
        req.price = snap.price
    else:
        rsi = req.indicators.get("rsi", 50.0)
        macd_hist = req.indicators.get("macd_hist", 0.0)
        supertrend_dir = req.indicators.get("supertrend_direction", 1)

    # 2. Worldwide news affecting this asset
    news = fetch_news(req.symbol)
    news_score: float = news["sentiment"]
    articles: List[Dict[str, Any]] = news["articles"]

    # 3. Combine technicals + news into a 0-100 rating
    base_rating = 50
    if rsi < 30:
        base_rating += 25
    elif rsi > 70:
        base_rating -= 20
    else:
        base_rating += int((rsi - 50) * 0.5)

    base_rating += 10 if macd_hist > 0 else -10
    base_rating += 15 if supertrend_dir == 1 else -15
    if snap:
        base_rating += max(-8, min(8, int(snap.change_pct)))  # recent momentum
    if articles:
        base_rating += int(round(news_score * 20))  # news can swing rating +/-20

    rating = max(5, min(95, base_rating))

    if rating >= 80:
        signal_type, confidence = "Strong Buy", 85
    elif rating >= 62:
        signal_type, confidence = "Buy", 72
    elif rating >= 45:
        signal_type, confidence = "Hold", 58
    elif rating >= 28:
        signal_type, confidence = "Sell", 72
    else:
        signal_type, confidence = "Strong Sell", 85

    # Agreement between chart and news boosts confidence, conflict lowers it
    tech_bull = (macd_hist > 0) + (supertrend_dir == 1) + (rsi < 70 and rsi > 40)
    if articles and abs(news_score) > 0.15:
        if (news_score > 0) == (tech_bull >= 2):
            confidence = min(95, confidence + 8)
        else:
            confidence = max(40, confidence - 12)

    probability_bullish = float(rating)
    probability_bearish = 100.0 - probability_bullish

    # 4. Levels from real highs/lows when available
    if snap:
        sup1, res1 = snap.support, snap.resistance
        sup2, res2 = sup1 * 0.97, res1 * 1.03
    else:
        sup1, sup2 = req.price * 0.97, req.price * 0.94
        res1, res2 = req.price * 1.03, req.price * 1.06

    is_buy = "Buy" in signal_type
    entry_target = req.price * 0.99 if is_buy else req.price * 1.01
    stop_loss = min(sup1, req.price * 0.97) if is_buy else max(res1, req.price * 1.03)
    take_profit = req.price * 1.06 if is_buy else req.price * 0.94

    news_label = "positive" if news_score > 0.15 else "negative" if news_score < -0.15 else "mixed/neutral"
    headlines = "\n".join(
        f"- [{a['source']}, {a['region']}] {a['title']} ({'+' if a['sentiment'] > 0 else ''}{a['sentiment']})"
        for a in articles[:6]
    )
    trend_txt = "uptrend (EMA20 above EMA50)" if supertrend_dir == 1 else "downtrend (EMA20 below EMA50)"

    # 5. Ask the LLM to explain the verdict (if loaded)
    qwen_text = ""
    if model is not None and tokenizer is not None and QWEN_AVAILABLE:
        try:
            prompt = (
                f"Asset: {req.symbol} ({req.timeframe}). Price {req.price:.2f}. "
                f"Trend: {trend_txt}. RSI {rsi:.1f}. MACD histogram {macd_hist:.3f}. "
                f"Support {sup1:.2f}, resistance {res1:.2f}.\n"
                f"News sentiment ({news['count']} articles worldwide): {news_label} ({news_score:+.2f}).\n"
                f"Latest headlines:\n{headlines or 'none found'}\n\n"
                f"Quantitative verdict: {signal_type} (rating {rating}/100, confidence {confidence}%).\n"
                + (f"User question: {req.question}\n" if req.question else "")
                + "In 4-6 short bullets: state clearly whether to BUY, SELL or HOLD now, "
                  "and explain using the chart, trend and the news. Mention the biggest risk."
            )
            messages = [
                {"role": "system", "content": "You are a quant trading copilot. Give a clear BUY/SELL/HOLD call grounded only in the data provided. Be concise. Not financial advice."},
                {"role": "user", "content": prompt},
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            model_inputs = tokenizer([text], return_tensors="pt")
            with torch.no_grad():  # pyright: ignore[reportPossiblyUnboundVariable]
                generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=90, do_sample=False)  # type: ignore[union-attr]
            generated_ids = [o[len(i):] for i, o in zip(model_inputs.input_ids, generated_ids)]
            qwen_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        except Exception as e:
            print(f"Qwen model generation failed: {str(e)}. Using fallback generator.")

    pattern_summary = ""
    if req.patterns:
        pattern_summary = f" Key pattern: {req.patterns[0]['name']} (Confidence {req.patterns[0].get('confidence')}%)."

    action = {"Strong Buy": "BUY", "Buy": "BUY", "Hold": "HOLD", "Sell": "SELL", "Strong Sell": "SELL"}[signal_type]
    plain_summary = (
        f"Verdict: {action}. {req.symbol} is in a {trend_txt} with RSI {rsi:.1f} and "
        f"{'bullish' if macd_hist > 0 else 'bearish'} MACD momentum. "
        f"Worldwide news sentiment is {news_label} ({news['count']} articles scanned).{pattern_summary}"
    )
    detailed_reasoning = (
        f"Chart: price {req.price:.2f}, support {sup1:.2f}, resistance {res1:.2f}"
        + (f", {snap.change_pct:+.1f}% over the last 20 bars" if snap else "")
        + f". Trend: {trend_txt}. News: {news_label} ({news_score:+.2f}). "
        f"Combined rating {rating}/100 -> {signal_type} at {confidence}% confidence."
        + (f"\nTop headlines:\n{headlines}" if headlines else "")
    )

    method_used = "Qwen 2.5 + live chart & global news" if qwen_text else "Live chart & global news (rule-based)"
    final_summary = f"{plain_summary}\n\n{qwen_text}" if qwen_text else plain_summary
    final_reasoning = detailed_reasoning

    return AnalysisResponse(
        rating=rating,
        signal_type=signal_type,
        confidence=confidence,
        trend="Bullish" if supertrend_dir == 1 else "Bearish",
        momentum="Strong Upward" if macd_hist > 0 else "Downward Consolidation",
        probability_bullish=probability_bullish,
        probability_bearish=probability_bearish,
        support_levels=[sup1, sup2],
        resistance_levels=[res1, res2],
        entry_target=entry_target,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_score="Low" if 40 < rsi < 60 else "Medium" if 30 < rsi < 70 else "High",
        position_size_suggestion="2.5% of total equity" if rating >= 62 or rating < 28 else "No position suggested (Neutral range)",
        plain_summary=final_summary,
        detailed_reasoning=final_reasoning,
        method=method_used,
        price=req.price,
        news=articles,
        news_sentiment=news_score,
        news_count=news["count"],
    )

def trend_strength(rsi_val: float) -> str:
    if rsi_val > 70: return "extremely strong / overbought"
    if rsi_val < 30: return "weakening / oversold"
    return "balanced / intermediate"

@app.get("/history")
def get_history(symbol: str, timeframe: str = "1D"):
    df = fetch_history_df(symbol, timeframe)
    if df is None:
        return []
    return [
        {
            "time": int(pd.Timestamp(ts).timestamp()),  # type: ignore[arg-type]
            "open": float(o), "high": float(h), "low": float(l), "close": float(c),
        }
        for ts, o, h, l, c in zip(
            df.index, df["Open"].tolist(), df["High"].tolist(), df["Low"].tolist(), df["Close"].tolist()
        )
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
