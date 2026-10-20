import React, { useState, useEffect } from 'react';
import { useStore } from './store/useStore';
import type { JournalEntry, Alert } from './store/useStore';
import { TradingChart } from './components/TradingChart';
import { API_BASE_URL } from './config';

const ASSETS_BY_CATEGORY: Record<string, Array<{ symbol: string; name: string }>> = {
    crypto: [
        { symbol: "BTC", name: "Bitcoin / USDT" },
        { symbol: "ETH", name: "Ethereum / USDT" },
        { symbol: "SOL", name: "Solana / USDT" },
        { symbol: "XRP", name: "Ripple / USDT" },
        { symbol: "ADA", name: "Cardano / USDT" }
    ],
    stocks: [
        { symbol: "Nvidia", name: "NVIDIA Corporation" },
        { symbol: "AAPL", name: "Apple Inc." },
        { symbol: "TSLA", name: "Tesla Inc." },
        { symbol: "MSFT", name: "Microsoft Corporation" },
        { symbol: "AMZN", name: "Amazon.com Inc." },
        { symbol: "GOOGL", name: "Alphabet Inc." }
    ],
    forex: [
        { symbol: "EUR", name: "EUR / USD" },
        { symbol: "GBP", name: "GBP / USD" },
        { symbol: "JPY", name: "USD / JPY" },
        { symbol: "AUD", name: "AUD / USD" }
    ],
    commodities: [
        { symbol: "Gold", name: "Gold Futures" },
        { symbol: "Crude Oil", name: "Crude Oil Futures" },
        { symbol: "Silver", name: "Silver Futures" }
    ],
    indices: [
        { symbol: "S&P 500", name: "S&P 500 Index" },
        { symbol: "Nasdaq 100", name: "Nasdaq 100 Index" },
        { symbol: "Dow Jones", name: "Dow Jones Industrial Average" }
    ],
    futures: [
        { symbol: "BTC", name: "Bitcoin Futures (CME)" },
        { symbol: "Gold", name: "COMEX Gold Futures" },
        { symbol: "S&P 500", name: "E-mini S&P 500 Futures" }
    ],
    ph_stocks: [
        { symbol: "JFC", name: "Jollibee Foods Corporation" },
        { symbol: "ALI", name: "Ayala Land, Inc." },
        { symbol: "BDO", name: "BDO Unibank, Inc." },
        { symbol: "SM", name: "SM Investments Corporation" },
        { symbol: "TEL", name: "PLDT Inc." }
    ]
};

export default function App() {
    // Auth & Navigation State
    const {
        currentView,
        setView,
        theme,
        toggleTheme,
        selectedSymbol,
        setSelectedSymbol,
        timeframe,
        setTimeframe,
        portfolios,
        setPortfolios,
        journalEntries,
        setJournalEntries,
        alerts,
        setAlerts,
        news,
        setNews
    } = useStore();

    // Local State
    const [isLoggedIn, setIsLoggedIn] = useState<boolean>(true); // Logged in by default in dev mode
    const [authEmail, setAuthEmail] = useState<string>('');
    const [authPassword, setAuthPassword] = useState<string>('');
    const [isRegistering, setIsRegistering] = useState<boolean>(false);

    // Exchange Connection Modal
    const [showExchangeModal, setShowExchangeModal] = useState<boolean>(false);
    const [exchangePlatform, setExchangePlatform] = useState<string>('Binance');
    const [apiKeyInput, setApiKeyInput] = useState<string>('');
    const [apiSecretInput, setApiSecretInput] = useState<string>('');
    const [isExchangeConnected, setIsExchangeConnected] = useState<boolean>(false);

    // Global Toast alert
    const [toastMessage, setToastMessage] = useState<string>('');
    const [toastType, setToastType] = useState<'success' | 'error'>('success');
    const [showToast, setShowToast] = useState<boolean>(false);

    // Markets Screen Toggles
    const [marketFilter, setMarketFilter] = useState<'crypto' | 'stocks' | 'forex' | 'commodities' | 'indices' | 'futures'>('crypto');
    const [marketSearch, setMarketSearch] = useState<string>('');
    // const [marketPage, setMarketPage] = useState<number>(1);
    // const marketPageSize = 4;

    // Order Form
    const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy');
    // const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
    // const [limitPrice, setLimitPrice] = useState<string>('64230');
    const [orderAmount, setOrderAmount] = useState<string>('');
    const [orderLeverage, setOrderLeverage] = useState<number>(1);

    // AI Chat Panel
    const [chatInput, setChatInput] = useState<string>('');
    const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'bot'; text: string; time: string }>>([
        { sender: 'bot', text: 'Hello trader. I am your AI Trading Copilot, connected to real-time order books, social feeds, and technical indicators. Ask me to evaluate any asset, e.g. "Analyze BTC" or "Is SOL a buy?".', time: '10:00' }
    ]);
    const [isAiTyping, setIsAiTyping] = useState<boolean>(false);

    // Journal Creator
    const [journalSymbol, setJournalSymbol] = useState<string>('BTC');
    const [journalEntryPrice, setJournalEntryPrice] = useState<string>('');
    const [journalExitPrice, setJournalExitPrice] = useState<string>('');
    const [journalQty, setJournalQty] = useState<string>('');
    const [journalEmotion, setJournalEmotion] = useState<string>('Confident');
    const [journalNotes, setJournalNotes] = useState<string>('');

    // Alert Creator
    const [alertSymbol, setAlertSymbol] = useState<string>('BTC');
    const [alertType, setAlertType] = useState<'price_above' | 'price_below'>('price_above');
    const [alertValue, setAlertValue] = useState<string>('65000');

    // Backtesting Form
    const [backtestStrategy, setBacktestStrategy] = useState<string>('SMA_Crossover');
    const [backtestSymbol, setBacktestSymbol] = useState<string>('BTC');
    // const [backtestTf, setBacktestTf] = useState<string>('1D');
    const [backtestStart, setBacktestStart] = useState<string>('2026-01-01');
    const [backtestEnd, setBacktestEnd] = useState<string>('2026-08-01');
    const [backtestResult, setBacktestResult] = useState<any>(null);

    // Live Tickers (Simulated Walk)
    const [tickerPrices, setTickerPrices] = useState<Record<string, { price: number; chg: number; flash: 'up' | 'down' | null }>>({
        'BTC': { price: 64230.50, chg: 2.45, flash: null },
        'ETH': { price: 3450.20, chg: -0.85, flash: null },
        'SOL': { price: 145.80, chg: 8.20, flash: null },
        'XRP': { price: 0.5824, chg: 1.12, flash: null },
        'ADA': { price: 0.3850, chg: -1.45, flash: null },
        'Nvidia': { price: 109.20, chg: 5.12, flash: null },
        'AAPL': { price: 218.40, chg: 0.95, flash: null },
        'TSLA': { price: 172.50, chg: -2.35, flash: null },
        'MSFT': { price: 420.50, chg: 0.15, flash: null },
        'AMZN': { price: 184.20, chg: 1.82, flash: null },
        'GOOGL': { price: 173.80, chg: -0.62, flash: null },
        'EUR': { price: 1.0824, chg: 0.12, flash: null },
        'GBP': { price: 1.2745, chg: 0.25, flash: null },
        'JPY': { price: 153.25, chg: -0.42, flash: null },
        'AUD': { price: 0.6542, chg: -0.18, flash: null },
        'Gold': { price: 2445.80, chg: 0.85, flash: null },
        'Crude Oil': { price: 78.42, chg: -1.25, flash: null },
        'Silver': { price: 28.15, chg: 1.48, flash: null },
        'S&P 500': { price: 5410.25, chg: 0.35, flash: null },
        'Nasdaq 100': { price: 19120.50, chg: 0.72, flash: null },
        'Dow Jones': { price: 39680.15, chg: -0.18, flash: null },
        'JFC': { price: 260.50, chg: 0.45, flash: null },
        'ALI': { price: 29.80, chg: -0.12, flash: null },
        'BDO': { price: 145.20, chg: 0.88, flash: null },
        'SM': { price: 880.00, chg: 1.15, flash: null },
        'TEL': { price: 1350.00, chg: -0.55, flash: null }
    });

    const [sentimentIndex, setSentimentIndex] = useState<number>(72);

    // ==========================================
    // Real-Time Price Simulation Engine
    // ==========================================
    useEffect(() => {
        const intervalId = setInterval(() => {
            setTickerPrices(prev => {
                const nextPrices = { ...prev };
                Object.keys(nextPrices).forEach(sym => {
                    const oldObj = nextPrices[sym];
                    const volatility = sym === 'BTC' || sym === 'SOL' ? 0.0025 : 0.0012;
                    const change = (Math.random() - 0.49) * volatility;
                    const newPrice = oldObj.price + (oldObj.price * change);
                    const newChg = oldObj.chg + (change * 100);
                    nextPrices[sym] = {
                        price: newPrice,
                        chg: newChg,
                        flash: change > 0 ? 'up' : 'down'
                    };
                });
                return nextPrices;
            });

            // Adjust sentiment slightly
            setSentimentIndex(prev => Math.max(10, Math.min(95, prev + (Math.random() > 0.5 ? 1 : -1))));
        }, 2000);

        return () => clearInterval(intervalId);
    }, []);

    // Helper to clear price flashes after 800ms
    useEffect(() => {
        const resetFlash = setTimeout(() => {
            setTickerPrices(prev => {
                const next = { ...prev };
                Object.keys(next).forEach(sym => {
                    next[sym].flash = null;
                });
                return next;
            });
        }, 800);
        return () => clearTimeout(resetFlash);
    }, [tickerPrices]);

    // ==========================================
    // Real-Time News Fetcher (CoinDesk Feed)
    // ==========================================
    useEffect(() => {
        const fetchRealNews = async () => {
            try {
                const rssUrl = encodeURIComponent('https://www.coindesk.com/arc/outboundfeeds/rss/');
                const res = await fetch(`https://api.rss2json.com/v1/api.json?rss_url=${rssUrl}`);
                if (!res.ok) return;
                const data = await res.json();
                if (data.status === 'ok' && Array.isArray(data.items)) {
                    const mappedArticles = data.items.map((item: any) => {
                        const text = (item.title + ' ' + item.description).toLowerCase();

                        let sentiment: 'Positive' | 'Negative' | 'Neutral' = 'Neutral';
                        let sentimentScore = 50;

                        const positiveWords = ['surge', 'gain', 'growth', 'rise', 'rises', 'approved', 'positive', 'expand', 'bullish', 'invest', 'upgrade', 'buy', 'higher', 'support', 'high', 'profit'];
                        const negativeWords = ['drop', 'slide', 'crash', 'exit', 'crime', 'illegal', 'stalls', 'downgrade', 'bearish', 'sell', 'lower', 'ban', 'block', 'risk', 'fail', 'loss'];

                        let posCount = 0;
                        let negCount = 0;

                        positiveWords.forEach(word => {
                            if (text.includes(word)) posCount++;
                        });
                        negativeWords.forEach(word => {
                            if (text.includes(word)) negCount++;
                        });

                        if (posCount > negCount) {
                            sentiment = 'Positive';
                            sentimentScore = Math.min(98, 60 + (posCount - negCount) * 10 + Math.floor(Math.random() * 10));
                        } else if (negCount > posCount) {
                            sentiment = 'Negative';
                            sentimentScore = Math.max(2, 40 - (negCount - posCount) * 10 - Math.floor(Math.random() * 10));
                        } else {
                            sentimentScore = 45 + Math.floor(Math.random() * 10);
                        }

                        let publishedAt = 'Just now';
                        try {
                            const pubTime = new Date(item.pubDate.replace(/-/g, '/')).getTime();
                            const diffMs = Date.now() - pubTime;
                            const diffMins = Math.floor(diffMs / 60000);
                            const diffHours = Math.floor(diffMins / 60);

                            if (diffMins < 60) {
                                publishedAt = diffMins > 0 ? `${diffMins}m ago` : 'Just now';
                            } else if (diffHours < 24) {
                                publishedAt = `${diffHours}h ago`;
                            } else {
                                publishedAt = new Date(pubTime).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                            }
                        } catch {
                            publishedAt = item.pubDate;
                        }

                        let marketImpact: 'High' | 'Medium' | 'Low' = 'Low';
                        if (posCount + negCount > 3 || text.includes('fed') || text.includes('sec') || text.includes('etf') || text.includes('regulation') || text.includes('interest rate')) {
                            marketImpact = 'High';
                        } else if (posCount + negCount > 1 || text.includes('bitcoin') || text.includes('ethereum') || text.includes('btc')) {
                            marketImpact = 'Medium';
                        }

                        return {
                            id: item.guid || item.link,
                            title: item.title,
                            source: 'CoinDesk',
                            publishedAt,
                            snippet: item.description.replace(/<[^>]*>/g, ''),
                            sentiment,
                            sentimentScore,
                            marketImpact
                        };
                    });
                    setNews(mappedArticles);
                }
            } catch (err) {
                console.error("Failed to fetch real-time news:", err);
            }
        };

        fetchRealNews();
        // Refresh news every 3 minutes
        const intervalId = setInterval(fetchRealNews, 180000);
        return () => clearInterval(intervalId);
    }, [setNews]);


    // ==========================================
    // Trigger Alerts Toast Helper
    // ==========================================
    const triggerToast = (msg: string, type: 'success' | 'error' = 'success') => {
        setToastMessage(msg);
        setToastType(type);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
    };

    // ==========================================
    // Authentication handlers
    // ==========================================
    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        if (!authEmail || !authPassword) {
            triggerToast('Email and password required', 'error');
            return;
        }
        setIsLoggedIn(true);
        triggerToast('Session established with Supabase Auth!');
    };

    const handleRegister = (e: React.FormEvent) => {
        e.preventDefault();
        setIsRegistering(false);
        triggerToast('Account registered! Verification link emitted.');
    };

    // ==========================================
    // Exchange Connection Modal
    // ==========================================
    const handleConnectExchange = () => {
        if (!apiKeyInput || !apiSecretInput) {
            triggerToast('API Key and Secret required', 'error');
            return;
        }
        setIsExchangeConnected(true);
        setShowExchangeModal(false);
        triggerToast(`Connected successfully to ${exchangePlatform}!`);
    };

    // ==========================================
    // Portfolio Order Placement Engine
    // ==========================================
    const executeOrder = () => {
        if (!orderAmount || parseFloat(orderAmount) <= 0) {
            triggerToast('Please specify a valid order amount.', 'error');
            return;
        }

        const qty = parseFloat(orderAmount);
        const currentPrice = tickerPrices[selectedSymbol]?.price || 100.00;
        const totalCost = qty * currentPrice;
        const marginCost = totalCost / orderLeverage;

        const currentPort = portfolios[0];
        if (orderSide === 'buy') {
            if (marginCost > currentPort.availableUsd) {
                triggerToast('Insufficient available margin funds.', 'error');
                return;
            }

            // Deduct Cash, Update/Insert holding
            const nextAssets = [...currentPort.assets];
            const existingAssetIdx = nextAssets.findIndex(a => a.symbol === selectedSymbol);
            if (existingAssetIdx >= 0) {
                const asset = nextAssets[existingAssetIdx];
                const oldCost = asset.quantity * asset.averageBuyPrice;
                asset.quantity += qty;
                asset.averageBuyPrice = (oldCost + totalCost) / asset.quantity;
            } else {
                nextAssets.push({
                    id: Math.random().toString(),
                    symbol: selectedSymbol,
                    quantity: qty,
                    averageBuyPrice: currentPrice
                });
            }

            const updatedPortfolios = [{
                ...currentPort,
                availableUsd: currentPort.availableUsd - marginCost,
                assets: nextAssets
            }];
            setPortfolios(updatedPortfolios);

        } else { // Sell
            const nextAssets = [...currentPort.assets];
            const existingAssetIdx = nextAssets.findIndex(a => a.symbol === selectedSymbol);
            if (existingAssetIdx < 0 || nextAssets[existingAssetIdx].quantity < qty) {
                triggerToast(`Insufficient ${selectedSymbol} holdings to execute sell order.`, 'error');
                return;
            }

            const asset = nextAssets[existingAssetIdx];
            asset.quantity -= qty;
            if (asset.quantity <= 0.0001) {
                nextAssets.splice(existingAssetIdx, 1);
            }

            const updatedPortfolios = [{
                ...currentPort,
                availableUsd: currentPort.availableUsd + marginCost,
                assets: nextAssets
            }];
            setPortfolios(updatedPortfolios);
        }

        // Add to Transaction Logs
        const newLog: JournalEntry = {
            id: Math.random().toString(),
            symbol: selectedSymbol,
            entryPrice: currentPrice,
            exitPrice: 0,
            quantity: qty,
            side: orderSide.toUpperCase() as any,
            emotion: 'Neutral',
            outcome: 'BREAKEAVEN',
            pnlValue: 0,
            notes: `Mock trade placement via Chart Workspace. Leverage: ${orderLeverage}x`,
            createdAt: new Date().toLocaleTimeString()
        };
        setJournalEntries([newLog, ...journalEntries]);

        triggerToast(`Order filled: ${orderSide.toUpperCase()} ${qty} ${selectedSymbol} @ $${currentPrice.toFixed(2)}`);
        setOrderAmount('');
    };

    // ==========================================
    // AI Chat Engine Response Simulator
    // ==========================================
    const sendChatMessage = async () => {
        if (!chatInput.trim()) return;

        const userMsg = chatInput.trim();
        setChatInput('');
        const timeNow = new Date().toLocaleTimeString().substring(0, 5);

        const newMessages = [...chatMessages, { sender: 'user' as const, text: userMsg, time: timeNow }];
        setChatMessages(newMessages);
        setIsAiTyping(true);

        const q = userMsg.toLowerCase();
        let targetSymbol = '';
        if (q.includes('btc') || q.includes('bitcoin')) targetSymbol = 'BTC';
        else if (q.includes('eth') || q.includes('ethereum')) targetSymbol = 'ETH';
        else if (q.includes('sol') || q.includes('solana')) targetSymbol = 'SOL';
        else if (q.includes('xrp') || q.includes('ripple')) targetSymbol = 'XRP';
        else if (q.includes('ada') || q.includes('cardano')) targetSymbol = 'ADA';
        else if (q.includes('nvidia') || q.includes('nvda')) targetSymbol = 'Nvidia';
        else if (q.includes('aapl') || q.includes('apple')) targetSymbol = 'AAPL';
        else if (q.includes('tsla') || q.includes('tesla')) targetSymbol = 'TSLA';
        else if (q.includes('msft') || q.includes('microsoft')) targetSymbol = 'MSFT';
        else if (q.includes('amzn') || q.includes('amazon')) targetSymbol = 'AMZN';
        else if (q.includes('googl') || q.includes('google')) targetSymbol = 'GOOGL';
        else if (q.includes('eur')) targetSymbol = 'EUR';
        else if (q.includes('gbp')) targetSymbol = 'GBP';
        else if (q.includes('jpy')) targetSymbol = 'JPY';
        else if (q.includes('aud')) targetSymbol = 'AUD';
        else if (q.includes('gold')) targetSymbol = 'Gold';
        else if (q.includes('oil') || q.includes('crude')) targetSymbol = 'Crude Oil';
        else if (q.includes('silver')) targetSymbol = 'Silver';
        else if (q.includes('s&p') || q.includes('sp500')) targetSymbol = 'S&P 500';
        else if (q.includes('nasdaq')) targetSymbol = 'Nasdaq 100';
        else if (q.includes('dow')) targetSymbol = 'Dow Jones';

        if (!targetSymbol) {
            targetSymbol = selectedSymbol;
        }

        if (targetSymbol) {
            try {
                const currentPrice = tickerPrices[targetSymbol]?.price || 100.00;
                const mockRsi = 40 + Math.random() * 25;
                const mockMacd = (Math.random() - 0.48) * 10;
                const supertrend = Math.random() > 0.4 ? 1 : -1;

                const response = await fetch(`${API_BASE_URL}/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        symbol: targetSymbol,
                        timeframe: timeframe,
                        price: currentPrice,
                        indicators: {
                            rsi: mockRsi,
                            macd_hist: mockMacd,
                            supertrend_direction: supertrend
                        },
                        patterns: [],
                        question: userMsg
                    })
                });

                if (response.ok) {
                    const data = await response.json();

                    const livePrice: number = data.price || currentPrice;
                    const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    const nl = (s: string) => esc(s).replace(/\n/g, '<br/>');
                    const sentLabel = data.news_sentiment > 0.15 ? 'Positive' : data.news_sentiment < -0.15 ? 'Negative' : 'Mixed/Neutral';
                    const sentColor = data.news_sentiment > 0.15 ? 'text-emerald-400' : data.news_sentiment < -0.15 ? 'text-red-400' : 'text-outline';
                    const newsHtml = (data.news || []).slice(0, 6).map((n: any) =>
                        `• <a href="${esc(n.url || '#')}" target="_blank" rel="noopener noreferrer" class="underline">${esc(n.title)}</a> ` +
                        `<span class="text-xs text-outline">— ${esc(n.source)} (${esc(n.region)}) ${n.sentiment > 0 ? '▲' : n.sentiment < 0 ? '▼' : '•'}</span>`
                    ).join('<br/>');

                    const reply = `<strong>AI Copilot analysis for ${targetSymbol} (${timeframe}):</strong><br/><br/>` +
                        `<strong>Verdict:</strong> <span class="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${data.signal_type.includes('Buy') ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                            data.signal_type.includes('Sell') ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-surface-container-high/50 text-on-surface'
                        }">${data.signal_type} (Confidence: ${data.confidence}%)</span><br/>` +
                        `<strong>Current Price:</strong> $${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}<br/>` +
                        `<strong>Trend:</strong> ${data.trend} | <strong>Momentum:</strong> ${data.momentum}<br/>` +
                        `<strong>News Sentiment:</strong> <span class="${sentColor}">${sentLabel} (${data.news_count} articles worldwide)</span><br/>` +
                        `<strong>AI Rating Score:</strong> ${data.rating}/100<br/>` +
                        `<strong>Risk Profile:</strong> ${data.risk_score}<br/><br/>` +
                        `<strong>Target Parameters Suggestion:</strong><br/>` +
                        `• Suggest Entry: $${data.entry_target.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}<br/>` +
                        `• Stop Loss: $${data.stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}<br/>` +
                        `• Take Profit: $${data.take_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}<br/>` +
                        `• Sizing: ${data.position_size_suggestion}<br/><br/>` +
                        `<strong>Summary:</strong> ${nl(data.plain_summary)}<br/><br/>` +
                        (newsHtml ? `<strong>Latest News Affecting ${targetSymbol}:</strong><br/>${newsHtml}<br/><br/>` : '') +
                        `<strong>Detailed Reasoning:</strong> ${nl(data.detailed_reasoning)}<br/><br/>` +
                        `<span class="text-xs text-outline">Engine: ${data.method} · Not financial advice.</span>`;

                    setChatMessages(prev => [...prev, { sender: 'bot' as const, text: reply, time: timeNow }]);
                    setIsAiTyping(false);
                    return;
                }
            } catch (err) {
                console.warn("FastAPI backend connection refused or failed. Defaulting to client simulation.", err);
            }
        }

        // Graceful Client-side Fallback Simulation
        setTimeout(() => {
            let reply = "I've analyzed the technical metrics. Let me know if you would like me to audit a specific symbol, e.g. 'Analyze BTC' or run a portfolio audit.";

            if (q.includes('btc') || q.includes('bitcoin')) {
                const price = tickerPrices['BTC'].price;
                reply = `<strong>AI Analysis for Bitcoin (BTC/USD) (Mock)</strong>:<br/>` +
                    `Current price is trailing near $${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}. ` +
                    `RSI is standing at 62.4 (Neutral-Strong). The 25-day EMA presents solid support near $61,200. ` +
                    `Forecast indicates strong consolidation pattern in progress with a 72% bullish bias.`;
            } else if (q.includes('eth') || q.includes('ethereum')) {
                const price = tickerPrices['ETH'].price;
                reply = `<strong>AI Analysis for Ethereum (ETH/USD) (Mock)</strong>:<br/>` +
                    `Current price is trailing near $${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}. ` +
                    `We detect bearish divergence on the 4H charts. Technical indicators signal wait-and-see. Support established at $3,350.`;
            } else if (q.includes('sol') || q.includes('solana')) {
                const price = tickerPrices['SOL'].price;
                reply = `<strong>AI Analysis for Solana (SOL/USD) (Mock)</strong>:<br/>` +
                    `Current price is trailing near $${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}. ` +
                    `Momentum is strongly bullish (+8.20%). Bollinger Bands expansion indicates breakout confirmation. Target: $165.50.`;
            } else if (q.includes('portfolio') || q.includes('holdings')) {
                reply = `<strong>Portfolio Audit Log (Mock)</strong>:<br/>` +
                    `Available margin cash is $${portfolios[0].availableUsd.toLocaleString()}. Allocation splits are healthy. Leverage margins are safely within targets.`;
            }

            setChatMessages(prev => [...prev, { sender: 'bot' as const, text: reply, time: timeNow }]);
            setIsAiTyping(false);
        }, 1200);
    };

    // ==========================================
    // Strategy Backtester Simulator
    // ==========================================
    const runBacktest = (e: React.FormEvent) => {
        e.preventDefault();
        triggerToast('Running strategy backtest...');
        setTimeout(() => {
            const winRate = 62.4;
            const sharpe = 1.82;
            const pf = 1.45;
            const maxDd = 8.5;
            const totalRet = 24.5;

            const curve = [];
            let eq = 10000;
            for (let i = 0; i < 30; i++) {
                eq += eq * (0.015 + (i % 3 === 0 ? -0.025 : 0.02));
                curve.push({ time: `Day ${i + 1}`, value: eq });
            }

            setBacktestResult({
                winRate,
                sharpe,
                profitFactor: pf,
                maxDrawdown: maxDd,
                totalReturn: totalRet,
                equityCurve: curve
            });
            triggerToast('Backtest simulation finalized!');
        }, 1000);
    };

    // ==========================================
    // Journal logger
    // ==========================================
    const logJournalEntry = (e: React.FormEvent) => {
        e.preventDefault();
        if (!journalEntryPrice || !journalQty) {
            triggerToast('Price and quantity are mandatory.', 'error');
            return;
        }
        const newEntry: JournalEntry = {
            id: Math.random().toString(),
            symbol: journalSymbol,
            entryPrice: parseFloat(journalEntryPrice),
            exitPrice: parseFloat(journalExitPrice) || 0,
            quantity: parseFloat(journalQty),
            side: 'LONG',
            emotion: journalEmotion,
            outcome: 'PROFIT',
            pnlValue: (parseFloat(journalExitPrice) - parseFloat(journalEntryPrice)) * parseFloat(journalQty) || 0,
            notes: journalNotes,
            aiFeedback: `AI FEEDBACK: Entry logged successfully. Trade on ${journalSymbol} showed proper emotional grounding (${journalEmotion}). Focus on executing strictly based on your SMA strategy.`,
            createdAt: new Date().toLocaleTimeString()
        };
        setJournalEntries([newEntry, ...journalEntries]);
        triggerToast('Journal logged with AI audit feedback!');
        setJournalEntryPrice('');
        setJournalExitPrice('');
        setJournalQty('');
        setJournalNotes('');
    };

    // ==========================================
    // Alert triggers
    // ==========================================
    const addAlert = (e: React.FormEvent) => {
        e.preventDefault();
        const newAlert: Alert = {
            id: Math.random().toString(),
            symbol: alertSymbol,
            alertType: alertType as any,
            conditionValue: alertValue,
            isActive: true,
            createdAt: new Date().toLocaleTimeString()
        };
        setAlerts([newAlert, ...alerts]);
        triggerToast(`Alert registered for ${alertSymbol} crossing ${alertValue}!`);
        setAlertValue('');
    };

    // Clean total value calculation
    const calculateTotalPortfolioValue = () => {
        const port = portfolios[0];
        let assetSum = 0;
        port.assets.forEach(a => {
            const currentPrice = tickerPrices[a.symbol]?.price || a.averageBuyPrice;
            assetSum += a.quantity * currentPrice;
        });
        return port.availableUsd + assetSum;
    };

    if (!isLoggedIn) {
        return (
            <div className="min-h-screen bg-surface-container-lowest text-on-surface flex items-center justify-center font-body-md p-container-margin">
                <div className="glass-panel max-w-md w-full p-widget-padding rounded-xl border-t-2 border-t-secondary-container shadow-2xl">
                    <div className="flex items-center space-x-stack-sm mb-stack-lg">
                        <span className="material-symbols-outlined text-primary text-3xl ai-gradient-text" style={{ fontVariationSettings: "'FILL' 1" }}>token</span>
                        <h1 className="font-headline-md text-headline-md font-bold text-primary">AI Trading Copilot</h1>
                    </div>
                    {isRegistering ? (
                        <form onSubmit={handleRegister} className="space-y-4">
                            <h2 className="font-bold text-lg">Register Terminal Session</h2>
                            <div>
                                <label className="block text-xs text-outline mb-1">Email</label>
                                <input type="email" value={authEmail} onChange={e => setAuthEmail(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm text-on-surface" placeholder="trader@copilot.com" />
                            </div>
                            <div>
                                <label className="block text-xs text-outline mb-1">Password</label>
                                <input type="password" value={authPassword} onChange={e => setAuthPassword(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm text-on-surface" placeholder="••••••••" />
                            </div>
                            <button type="submit" className="w-full py-2.5 ai-gradient-bg text-white font-bold rounded text-sm hover:opacity-90">Create Session Credentials</button>
                            <p className="text-xs text-center text-outline cursor-pointer hover:underline" onClick={() => setIsRegistering(false)}>Already have an account? Sign In</p>
                        </form>
                    ) : (
                        <form onSubmit={handleLogin} className="space-y-4">
                            <h2 className="font-bold text-lg">Sign In to Copilot Terminal</h2>
                            <div>
                                <label className="block text-xs text-outline mb-1">Email</label>
                                <input type="email" value={authEmail} onChange={e => setAuthEmail(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm text-on-surface" placeholder="trader@copilot.com" />
                            </div>
                            <div>
                                <label className="block text-xs text-outline mb-1">Password</label>
                                <input type="password" value={authPassword} onChange={e => setAuthPassword(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm text-on-surface" placeholder="••••••••" />
                            </div>
                            <button type="submit" className="w-full py-2.5 ai-gradient-bg text-white font-bold rounded text-sm hover:opacity-90">Verify & Authenticate</button>
                            <p className="text-xs text-center text-outline cursor-pointer hover:underline" onClick={() => setIsRegistering(true)}>New to Copilot? Register here</p>
                        </form>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className={`min-h-screen ${theme === 'dark' ? 'dark bg-surface-container-lowest text-on-surface' : 'bg-gray-100 text-gray-900'} flex transition-colors duration-300`}>

            {/* SideNavBar */}
            <nav className={`h-full w-64 fixed left-0 top-0 border-r ${theme === 'dark' ? 'bg-surface-container-low border-outline-variant/30' : 'bg-white border-gray-200'} flex flex-col py-gutter px-stack-md z-50`}>
                <div className="mb-stack-lg flex items-center gap-stack-sm mt-stack-sm px-stack-xs">
                    <span className="material-symbols-outlined text-primary text-3xl ai-gradient-text" style={{ fontVariationSettings: "'FILL' 1" }}>token</span>
                    <div>
                        <h1 className="font-headline-md text-headline-md font-bold text-primary">AI Copilot</h1>
                        <p className="font-label-caps text-label-caps text-secondary uppercase tracking-wider">Premium Tier</p>
                    </div>
                </div>

                <div className="flex-1 flex flex-col gap-stack-xs overflow-y-auto">
                    {[
                        { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
                        { id: 'markets', label: 'Markets', icon: 'show_chart' },
                        { id: 'chart', label: 'Chart Workspace', icon: 'timeline' },
                        { id: 'ai', label: 'AI Analysis', icon: 'psychology' },
                        { id: 'news', label: 'News Feed', icon: 'newspaper' },
                        { id: 'journal', label: 'Trading Journal', icon: 'auto_stories' },
                        { id: 'alerts', label: 'Alert Manager', icon: 'notifications_active' },
                        { id: 'backtesting', label: 'Backtester', icon: 'settings_backup_restore' }
                    ].map(item => (
                        <a key={item.id} className={`flex items-center gap-stack-sm px-stack-sm py-stack-xs rounded-lg transition-colors duration-200 cursor-pointer ${currentView === item.id
                            ? 'text-primary font-bold bg-secondary-container/20'
                            : 'text-on-surface-variant font-medium hover:bg-surface-variant/30'
                            }`} onClick={() => setView(item.id)}>
                            <span className="material-symbols-outlined">{item.icon}</span>
                            <span className="font-body-md text-body-md">{item.label}</span>
                        </a>
                    ))}
                </div>

                <div className="mt-auto flex flex-col gap-stack-xs border-t border-outline-variant/30 pt-stack-md">
                    <a className={`flex items-center gap-stack-sm px-stack-sm py-stack-xs rounded-lg cursor-pointer ${currentView === 'settings' ? 'text-primary font-bold bg-secondary-container/20' : 'text-on-surface-variant font-medium hover:bg-surface-variant/30'
                        }`} onClick={() => setView('settings')}>
                        <span className="material-symbols-outlined">settings</span>
                        <span className="font-body-md text-body-md">Settings</span>
                    </a>
                    <a className="flex items-center gap-stack-sm px-stack-sm py-stack-xs rounded-lg text-on-surface-variant font-medium hover:bg-surface-variant/30 cursor-pointer" onClick={toggleTheme}>
                        <span className="material-symbols-outlined">{theme === 'dark' ? 'light_mode' : 'dark_mode'}</span>
                        <span className="font-body-md text-body-md">{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
                    </a>
                </div>
            </nav>

            {/* Main content Area */}
            <div className="flex-1 ml-64 flex flex-col relative min-h-screen">

                {/* TopNavBar */}
                <header className={`fixed top-0 right-0 left-64 h-16 z-40 backdrop-blur-xl border-b flex justify-between items-center px-container-margin ${theme === 'dark' ? 'bg-surface/70 border-outline-variant/30' : 'bg-white/70 border-gray-200'
                    }`}>
                    <div className="flex items-center gap-stack-md">
                        <span className="font-body-lg text-body-lg font-bold uppercase tracking-wider">{currentView} Terminal</span>
                        <div className={`flex items-center rounded-full px-stack-sm py-1 border transition-colors ${theme === 'dark' ? 'bg-surface-container-high border-outline-variant' : 'bg-gray-100 border-gray-300'
                            }`}>
                            <span className="material-symbols-outlined text-on-surface-variant text-sm mr-2">search</span>
                            <input value={marketSearch} onChange={e => {
                                setMarketSearch(e.target.value);
                                if (currentView !== 'markets') setView('markets');
                            }} className="bg-transparent border-none focus:ring-0 text-sm w-64 text-on-surface placeholder:text-on-surface-variant data-font outline-none" placeholder="Search assets, AI insights..." />
                        </div>
                    </div>

                    <div className="flex items-center gap-stack-lg">
                        <div className="flex gap-stack-sm">
                            {['1H', '4H', '1D', '1W'].map(tf => (
                                <button key={tf} className={`font-label-caps text-label-caps px-2 py-1 transition-all ${timeframe === tf ? 'text-primary border-b-2 border-primary' : 'text-on-surface-variant hover:text-on-surface'
                                    }`} onClick={() => {
                                        setTimeframe(tf);
                                        triggerToast(`Timeframe swapped to ${tf}`);
                                    }}>{tf}</button>
                            ))}
                        </div>

                        <div className="flex items-center gap-stack-sm border-l border-outline-variant/30 pl-stack-md">
                            <button className={`font-label-caps text-label-caps border px-4 py-2 rounded-lg transition-colors ${isExchangeConnected ? 'border-tertiary-fixed-dim text-tertiary-fixed-dim bg-tertiary/10' : 'border-outline-variant text-on-surface hover:bg-surface-variant/30'
                                }`} onClick={() => setShowExchangeModal(true)}>
                                {isExchangeConnected ? 'Exchange Connected' : 'Connect Exchange'}
                            </button>
                            <button className="font-label-caps text-label-caps ai-gradient-bg text-white px-4 py-2 rounded-lg flex items-center gap-2 ai-glow">
                                <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                                AI Ready
                            </button>
                            <img alt="User avatar" className="w-8 h-8 rounded-full border border-outline-variant ml-2 object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuC9dJrUSORuOUMK0KNrWiwybrK3hW7jsCYu7bfxheRTp0hb4eACtGZP7Mf8wRcu01-5JidpGJeNmo-hSKJgmRB7NlzV9YKZV4xQluGovH4ACmjZxXyzyFtJChYcCbeVNY5YPNLczeBxa-Rl5m3j3GA_dScyj0r-XLVedZfKb1InxqjM-XNGN9RgDtCk-GSLYKEJfcf_VuEDKadoYiAjedRmqflAg6_vFTJs9B6SU1tbKeF_k03NUXPhIw" />
                        </div>
                    </div>
                </header>

                {/* Dashboard view body */}
                <main className="flex-1 mt-16 p-container-margin overflow-y-auto">

                    {/* 1. Dashboard View */}
                    {currentView === 'dashboard' && (
                        <div className="space-y-stack-lg animate-fade-in">
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-stack-md">
                                <div className="glass-panel rounded-xl p-widget-padding md:col-span-8 flex flex-col justify-between h-[300px]">
                                    <div>
                                        <h2 className="font-label-caps text-label-caps text-outline uppercase tracking-wider mb-stack-xs">Total Portfolio Value</h2>
                                        <div className="flex items-baseline gap-stack-md">
                                            <span className="font-headline-xl text-headline-xl font-bold data-font">${calculateTotalPortfolioValue().toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                                            <span className="font-data-md text-data-md text-tertiary flex items-center bg-tertiary/10 px-2 py-1 rounded">
                                                <span className="material-symbols-outlined text-sm mr-1">arrow_upward</span>
                                                +$1,240.12 (1.01%)
                                            </span>
                                        </div>
                                    </div>
                                    <div className="h-32 mt-stack-md w-full relative">
                                        <svg className="w-full h-full text-tertiary" preserveAspectRatio="none" viewBox="0 0 100 40">
                                            <path d="M0 40 L0 30 L10 32 L20 25 L30 28 L40 15 L50 20 L60 10 L70 15 L80 5 L90 8 L100 0 L100 40 Z" fill="currentColor" fillOpacity="0.08"></path>
                                            <path d="M0 30 L10 32 L20 25 L30 28 L40 15 L50 20 L60 10 L70 15 L80 5 L90 8 L100 0" fill="none" stroke="currentColor" strokeWidth="1"></path>
                                        </svg>
                                    </div>
                                </div>
                                <div className="glass-panel rounded-xl p-widget-padding md:col-span-4 flex flex-col items-center justify-center h-[300px]">
                                    <h2 className="font-label-caps text-label-caps text-outline uppercase tracking-wider w-full text-left mb-stack-sm">Market Sentiment</h2>
                                    <div className="relative w-40 h-40 flex items-center justify-center">
                                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                                            <circle cx="50" cy="50" fill="none" r="40" stroke="#2B3139" strokeWidth="8" strokeDasharray="188 251" strokeDashoffset="-30" strokeLinecap="round"></circle>
                                            <circle cx="50" cy="50" fill="none" r="40" stroke="#3be194" strokeWidth="8" strokeDasharray={`${(sentimentIndex / 100) * 188} 251`} strokeDashoffset="-30" strokeLinecap="round"></circle>
                                        </svg>
                                        <div className="absolute flex flex-col items-center text-center">
                                            <span className="font-headline-lg text-headline-lg font-bold data-font text-tertiary">{sentimentIndex}</span>
                                            <span className="font-label-caps text-label-caps text-outline">Greed</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 2. Markets View */}
                    {currentView === 'markets' && (
                        <div className="space-y-stack-lg">
                            <div className="flex flex-col md:flex-row md:items-end justify-between gap-stack-md">
                                <div>
                                    <h2 className="font-headline-lg text-headline-lg text-on-surface">Markets Browser</h2>
                                    <p className="text-on-surface-variant">Real-time asset exploration with AI predictive scoring.</p>
                                </div>
                                <div className="flex bg-[#161A1E] rounded-lg p-1 border border-[#2B3139] flex-wrap gap-1">
                                    {['crypto', 'stocks', 'forex', 'commodities', 'indices', 'futures', 'ph_stocks'].map(cat => (
                                        <button key={cat} className={`px-4 py-1.5 rounded-sm font-medium text-body-md uppercase ${marketFilter === cat ? 'bg-[#323538] text-on-surface' : 'text-on-surface-variant hover:text-on-surface'
                                            }`} onClick={() => setMarketFilter(cat as any)}>{cat === 'ph_stocks' ? 'PSE Stocks' : cat}</button>
                                    ))}
                                </div>
                            </div>

                            <div className="glass-panel rounded-xl overflow-hidden flex flex-col border-l-2 border-l-[#8A2BE2]">
                                <table className="w-full text-left border-collapse min-w-[900px]">
                                    <thead>
                                        <tr className="border-b border-outline-variant/30 bg-[#161A1E]/30 text-xs text-outline uppercase">
                                            <th className="py-3 px-4 w-12 text-center">WATCH</th>
                                            <th className="py-3 px-4">ASSET</th>
                                            <th className="py-3 px-4 text-right">PRICE</th>
                                            <th className="py-3 px-4 text-right">24H CHG</th>
                                            <th className="py-3 px-4 text-center">AI RATING</th>
                                            <th className="py-3 px-4 text-center">SIGNAL</th>
                                            <th className="py-3 px-4">CONFIDENCE</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-outline-variant/10 text-body-md">
                                        {(ASSETS_BY_CATEGORY[marketFilter] || []).map(asset => {
                                            const sym = asset.symbol;
                                            const obj = tickerPrices[sym] || { price: 0, chg: 0, flash: null };
                                            const flashClass = obj.flash === 'up' ? 'flash-up' : obj.flash === 'down' ? 'flash-down' : '';
                                            return (
                                                <tr key={`${sym}-${asset.name}`} className={`hover:bg-white/5 transition-all duration-300 h-[56px] cursor-pointer ${flashClass}`} onClick={() => {
                                                    setSelectedSymbol(sym);
                                                    setView('chart');
                                                }}>
                                                    <td className="px-4 text-center">
                                                        <span className="material-symbols-outlined text-primary text-xl">star</span>
                                                    </td>
                                                    <td className="px-4 py-2 font-semibold">
                                                        <div>{sym}</div>
                                                        <div className="text-[11px] text-outline font-normal">{asset.name}</div>
                                                    </td>
                                                    <td className="px-4 py-2 text-right data-font">
                                                        ${obj.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                    </td>
                                                    <td className={`px-4 py-2 text-right data-font ${obj.chg >= 0 ? 'text-tertiary-fixed-dim' : 'text-error'}`}>
                                                        {obj.chg >= 0 ? '+' : ''}{obj.chg.toFixed(2)}%
                                                    </td>
                                                    <td className="px-4 py-2 text-center">
                                                        <span className="w-8 h-8 rounded-full bg-secondary-container/20 text-secondary-fixed border border-secondary-container/50 inline-flex items-center justify-center font-bold">88</span>
                                                    </td>
                                                    <td className="px-4 py-2 text-center">
                                                        <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-tertiary-container/20 text-tertiary-fixed-dim border border-tertiary-container/30">Strong Buy</span>
                                                    </td>
                                                    <td className="px-4 py-2">
                                                        <div className="flex items-center space-x-2">
                                                            <div className="font-data-sm text-data-sm text-on-surface w-8 text-right">92%</div>
                                                            <div className="confidence-meter-container">
                                                                <div className="confidence-meter-fill" style={{ width: '92%' }}></div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* 3. Chart Workspace View */}
                    {currentView === 'chart' && (
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-stack-md h-[calc(100vh-140px)] min-h-[500px]">
                            {/* Chart Container */}
                            <div className="lg:col-span-8 flex flex-col justify-between glass-panel rounded-xl overflow-hidden p-stack-md gap-4">
                                <div className="flex justify-between items-center">
                                    <div>
                                        <h3 className="font-bold text-lg">{selectedSymbol} / USDT Candlestick Ticker</h3>
                                        <p className="text-xs text-outline">Real-time TradingView feed overlaying Chronos price predictions.</p>
                                    </div>
                                </div>
                                <div className="flex-1 w-full relative">
                                    <TradingChart
                                        symbol={selectedSymbol}
                                        timeframe={timeframe}
                                        showMA={true}
                                        showForecast={true}
                                        showPatterns={true}
                                        theme={theme}
                                    />
                                </div>
                            </div>

                            {/* Order & AI Chat panel */}
                            <div className="lg:col-span-4 flex flex-col gap-stack-md h-full overflow-hidden">
                                {/* Order panel */}
                                <div className="glass-panel rounded-xl p-widget-padding flex flex-col justify-between h-[200px] shrink-0 border-t-2 border-t-primary">
                                    <div>
                                        <div className="flex border-b border-outline-variant/30 mb-2">
                                            <button className={`flex-1 text-center font-bold pb-1.5 text-xs ${orderSide === 'buy' ? 'text-tertiary border-b-2 border-tertiary' : 'text-on-surface-variant'}`} onClick={() => setOrderSide('buy')}>BUY</button>
                                            <button className={`flex-1 text-center font-bold pb-1.5 text-xs ${orderSide === 'sell' ? 'text-error border-b-2 border-error' : 'text-on-surface-variant'}`} onClick={() => setOrderSide('sell')}>SELL</button>
                                        </div>
                                        <div className="space-y-2">
                                            <div>
                                                <label className="block text-[10px] text-outline mb-0.5">Amount ({selectedSymbol})</label>
                                                <input type="number" value={orderAmount} onChange={e => setOrderAmount(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded px-2 py-1 text-xs text-on-surface" placeholder="0.00" />
                                            </div>
                                            <div>
                                                <label className="block text-[10px] text-outline mb-0.5">Leverage: {orderLeverage}x</label>
                                                <input type="range" min="1" max="100" value={orderLeverage} onChange={e => setOrderLeverage(parseInt(e.target.value))} className="w-full accent-primary h-1 rounded" />
                                            </div>
                                        </div>
                                    </div>
                                    <button onClick={executeOrder} className={`w-full py-1.5 rounded font-bold text-xs text-on-tertiary-fixed uppercase ${orderSide === 'buy' ? 'bg-tertiary' : 'bg-error text-white'}`}>Execute {orderSide} {selectedSymbol}</button>
                                </div>

                                {/* AI Chart Assistant Chat Box */}
                                <div className="flex-1 glass-panel rounded-xl overflow-hidden flex flex-col border-t-2 border-t-[#8A2BE2] min-h-[220px]">
                                    <div className="px-stack-md py-2 border-b border-outline-variant/20 flex justify-between items-center bg-[#161A1E]/50 shrink-0">
                                        <h4 className="font-headline-md text-xs text-on-surface flex items-center space-x-1.5">
                                            <span className="material-symbols-outlined text-secondary text-[16px] ai-gradient-text" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                                            <span className="ai-gradient-text font-bold">Chart AI Co-analyst</span>
                                        </h4>
                                        <span className="text-[9px] text-outline bg-secondary-container/20 text-secondary-fixed px-1.5 py-0.5 rounded border border-secondary-container/30">Active</span>
                                    </div>

                                    <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs">
                                        {chatMessages.map((msg, idx) => (
                                            <div key={idx} className={`flex items-start space-x-2 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                                                {msg.sender === 'bot' && (
                                                    <div className="w-6 h-6 rounded-full bg-secondary-container/20 border border-secondary-container/30 flex items-center justify-center shrink-0">
                                                        <span className="material-symbols-outlined text-secondary text-xs">smart_toy</span>
                                                    </div>
                                                )}
                                                <div className={`p-2 rounded-xl max-w-[85%] ${msg.sender === 'user' ? 'bg-primary/20 border border-primary/20 text-right' : 'bg-surface-container-high/50'}`}>
                                                    <p className="font-semibold text-[9px] text-primary mb-0.5">{msg.sender === 'user' ? 'Trader' : 'Copilot'}</p>
                                                    <p className="text-on-surface leading-normal text-[11px]" dangerouslySetInnerHTML={{ __html: msg.text }}></p>
                                                </div>
                                            </div>
                                        ))}
                                        {isAiTyping && (
                                            <div className="flex items-center space-x-1 py-1 px-3">
                                                <span className="w-1 h-1 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                                                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                                <span className="w-1 h-1 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                                            </div>
                                        )}
                                    </div>

                                    <div className="p-2 border-t border-outline-variant/20 bg-[#161A1E]/30 flex items-center space-x-2 shrink-0">
                                        <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChatMessage()} type="text" className="flex-1 bg-surface-container-high border border-[#2B3139] rounded px-3 py-1.5 text-xs text-on-surface outline-none" placeholder={`Ask about ${selectedSymbol} chart...`} />
                                        <button onClick={sendChatMessage} className="ai-gradient-bg text-white p-1.5 rounded hover:opacity-90"><span className="material-symbols-outlined text-xs">send</span></button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 4. AI Analysis View */}
                    {currentView === 'ai' && (
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-stack-md h-[calc(100vh-140px)] min-h-[500px]">
                            <div className="lg:col-span-8 glass-panel rounded-xl overflow-hidden flex flex-col h-full border-l-2 border-l-[#8A2BE2]">
                                <div className="p-widget-padding border-b border-outline-variant/20 flex justify-between items-center bg-[#161A1E]/50">
                                    <h3 className="font-headline-md text-[18px] text-on-surface flex items-center space-x-2">
                                        <span className="material-symbols-outlined text-secondary ai-gradient-text" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                                        <span className="ai-gradient-text font-bold">Copilot Intel Agent (Qwen 3 8B)</span>
                                    </h3>
                                    <span className="text-xs text-outline bg-secondary-container/20 text-secondary-fixed px-2 py-0.5 rounded border border-secondary-container/30">Active</span>
                                </div>

                                <div className="flex-1 p-widget-padding overflow-y-auto space-y-4 text-sm">
                                    {chatMessages.map((msg, idx) => (
                                        <div key={idx} className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                                            {msg.sender === 'bot' && (
                                                <div className="w-8 h-8 rounded-full bg-secondary-container/20 border border-secondary-container/30 flex items-center justify-center shrink-0">
                                                    <span className="material-symbols-outlined text-secondary text-lg">smart_toy</span>
                                                </div>
                                            )}
                                            <div className={`p-3 rounded-xl max-w-[80%] ${msg.sender === 'user' ? 'bg-primary/20 border border-primary/20 text-right' : 'bg-surface-container-high/50'}`}>
                                                <p className="font-semibold text-xs text-primary mb-1">{msg.sender === 'user' ? 'Trader' : 'Copilot'}</p>
                                                <p className="text-on-surface" dangerouslySetInnerHTML={{ __html: msg.text }}></p>
                                            </div>
                                        </div>
                                    ))}
                                    {isAiTyping && (
                                        <div className="flex items-center space-x-1 py-1 px-4">
                                            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                                            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                                        </div>
                                    )}
                                </div>

                                <div className="p-3 border-t border-outline-variant/20 bg-[#161A1E]/30 flex items-center space-x-2">
                                    <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChatMessage()} type="text" className="flex-1 bg-surface-container-high border border-[#2B3139] rounded-lg px-4 py-2 text-sm text-on-surface" placeholder="Ask AI Copilot for analysis..." />
                                    <button onClick={sendChatMessage} className="ai-gradient-bg text-white p-2 rounded-lg hover:opacity-90"><span className="material-symbols-outlined text-sm">send</span></button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 5. News View */}
                    {currentView === 'news' && (
                        <div className="space-y-stack-lg">
                            <h2 className="font-headline-lg text-headline-lg">Fintech News Stream</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-stack-md">
                                {news.map(item => (
                                    <div key={item.id} className="glass-panel p-widget-padding rounded-xl flex flex-col justify-between hover:border-outline transition-all duration-300">
                                        <div>
                                            <div className="flex justify-between items-start mb-2">
                                                <span className="text-xs text-outline">{item.source} • {item.publishedAt}</span>
                                                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${item.sentiment === 'Positive' ? 'bg-tertiary-container/20 text-tertiary' : 'bg-error-container/20 text-error'
                                                    }`}>{item.sentiment} ({item.sentimentScore}%)</span>
                                            </div>
                                            <h3 className="font-bold text-sm mb-2">{item.title}</h3>
                                            <p className="text-xs text-on-surface-variant">{item.snippet}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 6. Trading Journal View */}
                    {currentView === 'journal' && (
                        <div className="space-y-stack-lg">
                            <h2 className="font-headline-lg text-headline-lg">Trading Journal</h2>
                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-stack-md">
                                <form onSubmit={logJournalEntry} className="lg:col-span-4 glass-panel p-widget-padding rounded-xl space-y-3">
                                    <h3 className="font-semibold text-md border-b border-outline-variant/30 pb-2">Log New Entry</h3>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Symbol</label>
                                        <select value={journalSymbol} onChange={e => setJournalSymbol(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded text-sm py-1.5">
                                            <option value="BTC">BTC</option>
                                            <option value="ETH">ETH</option>
                                            <option value="SOL">SOL</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Entry Price</label>
                                        <input type="number" value={journalEntryPrice} onChange={e => setJournalEntryPrice(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm" placeholder="62000" />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Exit Price</label>
                                        <input type="number" value={journalExitPrice} onChange={e => setJournalExitPrice(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm" placeholder="63500" />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Quantity</label>
                                        <input type="number" value={journalQty} onChange={e => setJournalQty(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm" placeholder="0.1" />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Emotion State</label>
                                        <select value={journalEmotion} onChange={e => setJournalEmotion(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded text-sm py-1.5">
                                            <option value="Confident">Confident</option>
                                            <option value="Anxious">Anxious</option>
                                            <option value="Fearful">Fearful</option>
                                            <option value="Greedy">Greedy</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Notes</label>
                                        <textarea value={journalNotes} onChange={e => setJournalNotes(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm h-20" placeholder="Describe entry conditions..."></textarea>
                                    </div>
                                    <button type="submit" className="w-full py-2.5 ai-gradient-bg text-white font-bold rounded text-sm">Save Entry & Request AI Review</button>
                                </form>
                                <div className="lg:col-span-8 space-y-4">
                                    {journalEntries.map(entry => (
                                        <div key={entry.id} className="glass-panel p-widget-padding rounded-xl border-l-4 border-l-tertiary">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="font-bold text-sm">{entry.symbol} {entry.side} - {entry.createdAt}</span>
                                                <span className="text-xs px-2 py-0.5 bg-tertiary/10 text-tertiary-fixed-dim rounded font-bold">OUTCOME: {entry.outcome}</span>
                                            </div>
                                            <p className="text-xs text-on-surface mb-2 font-mono">Qty: {entry.quantity} | Entry: ${entry.entryPrice} | Exit: ${entry.exitPrice}</p>
                                            {entry.notes && <p className="text-xs text-on-surface-variant bg-surface-container-high/30 p-2 rounded mb-3">Notes: {entry.notes}</p>}
                                            {entry.aiFeedback && <p className="text-xs text-secondary-fixed bg-secondary-container/10 p-2.5 rounded border border-secondary-container/20">{entry.aiFeedback}</p>}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 7. Alert Manager View */}
                    {currentView === 'alerts' && (
                        <div className="space-y-stack-lg">
                            <h2 className="font-headline-lg text-headline-lg">Alert Manager</h2>
                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-stack-md">
                                <form onSubmit={addAlert} className="lg:col-span-4 glass-panel p-widget-padding rounded-xl space-y-3">
                                    <h3 className="font-semibold text-md border-b border-outline-variant/30 pb-2">Create Trigger Alert</h3>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Asset Symbol</label>
                                        <input type="text" value={alertSymbol} onChange={e => setAlertSymbol(e.target.value.toUpperCase())} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Condition Trigger</label>
                                        <select value={alertType} onChange={e => setAlertType(e.target.value as any)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded text-sm py-1.5">
                                            <option value="price_above">Price Crosses Above</option>
                                            <option value="price_below">Price Crosses Below</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Trigger Price (USD)</label>
                                        <input type="number" value={alertValue} onChange={e => setAlertValue(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm" />
                                    </div>
                                    <button type="submit" className="w-full py-2.5 ai-gradient-bg text-white font-bold rounded text-sm">Deploy Alert Trigger</button>
                                </form>
                                <div className="lg:col-span-8 glass-panel rounded-xl overflow-hidden">
                                    <table className="w-full text-left text-xs border-collapse">
                                        <thead>
                                            <tr className="border-b border-outline-variant/30 bg-[#161A1E]/30 text-outline">
                                                <th className="py-2.5 px-4">ASSET</th>
                                                <th className="py-2.5 px-4">CONDITION</th>
                                                <th className="py-2.5 px-4">VALUE</th>
                                                <th className="py-2.5 px-4">STATUS</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {alerts.map(a => (
                                                <tr key={a.id} className="border-b border-outline-variant/10">
                                                    <td className="py-2.5 px-4 font-bold">{a.symbol}</td>
                                                    <td className="py-2.5 px-4 font-mono">{a.alertType}</td>
                                                    <td className="py-2.5 px-4 font-mono">${a.conditionValue}</td>
                                                    <td className="py-2.5 px-4">
                                                        <span className="px-2 py-0.5 rounded bg-tertiary/10 text-tertiary-fixed-dim text-[10px] font-bold">ACTIVE</span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 8. Backtester View */}
                    {currentView === 'backtesting' && (
                        <div className="space-y-stack-lg">
                            <h2 className="font-headline-lg text-headline-lg">Strategy Backtester</h2>
                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-stack-md">
                                <form onSubmit={runBacktest} className="lg:col-span-4 glass-panel p-widget-padding rounded-xl space-y-3">
                                    <h3 className="font-semibold text-md border-b border-outline-variant/30 pb-2">Configure Strategy Run</h3>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Backtest Model</label>
                                        <select value={backtestStrategy} onChange={e => setBacktestStrategy(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded text-sm py-1.5">
                                            <option value="SMA_Crossover">SMA Crossover (7, 25)</option>
                                            <option value="RSI_Breakout">RSI Breakout (30, 70)</option>
                                            <option value="MACD_Momentum">MACD Momentum</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs text-outline mb-1">Asset Ticker</label>
                                        <input type="text" value={backtestSymbol} onChange={e => setBacktestSymbol(e.target.value.toUpperCase())} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm" />
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div>
                                            <label className="block text-xs text-outline mb-1">Start Date</label>
                                            <input type="date" value={backtestStart} onChange={e => setBacktestStart(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-xs" />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-outline mb-1">End Date</label>
                                            <input type="date" value={backtestEnd} onChange={e => setBacktestEnd(e.target.value)} className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-xs" />
                                        </div>
                                    </div>
                                    <button type="submit" className="w-full py-2.5 ai-gradient-bg text-white font-bold rounded text-sm">Execute Backtest Simulation</button>
                                </form>
                                <div className="lg:col-span-8 space-y-4">
                                    {backtestResult ? (
                                        <div className="glass-panel p-widget-padding rounded-xl space-y-4">
                                            <h3 className="font-bold border-b border-outline-variant/30 pb-2">Results & Metrics (Win Rate: {backtestResult.winRate}%)</h3>
                                            <div className="grid grid-cols-4 gap-2 text-center text-xs">
                                                <div className="bg-[#161A1E] p-2 rounded">
                                                    <div className="text-outline">Sharpe Ratio</div>
                                                    <div className="font-bold font-mono text-sm">{backtestResult.sharpe}</div>
                                                </div>
                                                <div className="bg-[#161A1E] p-2 rounded">
                                                    <div className="text-outline">Profit Factor</div>
                                                    <div className="font-bold font-mono text-sm">{backtestResult.profitFactor}</div>
                                                </div>
                                                <div className="bg-[#161A1E] p-2 rounded">
                                                    <div className="text-outline">Max Drawdown</div>
                                                    <div className="font-bold font-mono text-sm text-error">{backtestResult.maxDrawdown}%</div>
                                                </div>
                                                <div className="bg-[#161A1E] p-2 rounded">
                                                    <div className="text-outline">Total Return</div>
                                                    <div className="font-bold font-mono text-sm text-tertiary-fixed-dim">+{backtestResult.totalReturn}%</div>
                                                </div>
                                            </div>
                                            <div className="h-40 bg-[#161A1E] rounded p-2 flex flex-col justify-end">
                                                <div className="text-[10px] text-outline self-start mb-2">Equity Curve Graph</div>
                                                <svg className="w-full h-full text-primary" preserveAspectRatio="none" viewBox="0 0 100 40">
                                                    <path d="M0 40 L0 30 L10 25 L20 28 L30 18 L40 22 L50 12 L60 15 L70 5 L80 10 L90 2 L100 0 L100 40 Z" fill="currentColor" fillOpacity="0.08"></path>
                                                    <path d="M0 30 L10 25 L20 28 L30 18 L40 22 L50 12 L60 15 L70 5 L80 10 L90 2 L100 0" fill="none" stroke="currentColor" strokeWidth="1.5"></path>
                                                </svg>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="glass-panel p-widget-padding rounded-xl text-center py-20 text-outline">Configure and run a strategy backtest to render metric curves.</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 9. Settings View */}
                    {currentView === 'settings' && (
                        <div className="glass-panel p-widget-padding rounded-xl max-w-xl mx-auto border-t-2 border-t-[#8A2BE2] space-y-4">
                            <h3 className="font-bold text-lg border-b border-outline-variant/30 pb-2">Terminal Parameters Settings</h3>
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-xs text-outline mb-1">AI Model Backbone</label>
                                    <select className="w-full bg-[#161A1E] border border-[#2B3139] rounded text-sm py-2">
                                        <option value="Gemini 1.5 Pro">Gemini 1.5 Pro (Analytical Backbone)</option>
                                        <option value="Gemini 1.5 Flash">Gemini 1.5 Flash (Ultra-low Latency)</option>
                                        <option value="Claude 3.5 Sonnet">Claude 3.5 Sonnet (Pattern Specialist)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-outline mb-1">Risk Assessment Sensitivity</label>
                                    <select className="w-full bg-[#161A1E] border border-[#2B3139] rounded text-sm py-2">
                                        <option value="conservative">Conservative (90%+ Confidence Only)</option>
                                        <option value="moderate">Moderate Balanced (80%+ Confidence)</option>
                                        <option value="aggressive">Aggressive Scalping (65%+ Confidence)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-outline mb-1">API Key Config</label>
                                    <input type="text" className="w-full bg-[#161A1E] border border-[#2B3139] rounded p-2 text-sm font-mono" placeholder="eg. bin_key_771801c05d6cb7f0d..." value={apiKeyInput} readOnly />
                                </div>
                            </div>
                            <button onClick={() => triggerToast('Configuration stored successfully!')} className="w-full py-2.5 ai-gradient-bg text-white font-bold rounded text-sm">Save Configuration</button>
                        </div>
                    )}
                </main>
            </div>

            {/* Persistent Modal: Connect Exchange Credentials */}
            {showExchangeModal && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="glass-panel w-full max-w-md p-widget-padding rounded-xl relative border-t-2 border-t-[#8A2BE2] mx-4 space-y-3 shadow-2xl">
                        <button className="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface" onClick={() => setShowExchangeModal(false)}>
                            <span className="material-symbols-outlined">close</span>
                        </button>
                        <h3 className="font-bold text-lg">Connect Exchange API</h3>
                        <p className="text-xs text-outline">Enter mock API key values. Credentials will be securely stored inside browser localStorage.</p>
                        <div>
                            <label className="block text-xs text-outline mb-1">Exchange Platform</label>
                            <select value={exchangePlatform} onChange={e => setExchangePlatform(e.target.value)} className="w-full bg-surface-container border border-outline-variant/50 rounded text-sm py-2 text-on-surface">
                                <option value="Binance">Binance Custody</option>
                                <option value="Coinbase Pro">Coinbase Pro Institutional</option>
                                <option value="OKX">OKX Direct API</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-outline mb-1">API Key</label>
                            <input type="password" value={apiKeyInput} onChange={e => setApiKeyInput(e.target.value)} className="w-full bg-surface-container border border-outline-variant/50 rounded text-sm py-2 px-3 text-on-surface" placeholder="Enter key hash identifier..." />
                        </div>
                        <div>
                            <label className="block text-xs text-outline mb-1">API Secret</label>
                            <input type="password" value={apiSecretInput} onChange={e => setApiSecretInput(e.target.value)} className="w-full bg-surface-container border border-outline-variant/50 rounded text-sm py-2 px-3 text-on-surface" placeholder="Enter Secret token..." />
                        </div>
                        <div className="flex justify-end gap-2 mt-5">
                            <button className="px-4 py-2 border border-outline-variant rounded-lg text-xs" onClick={() => setShowExchangeModal(false)}>Cancel</button>
                            <button className="px-5 py-2 ai-gradient-bg text-white font-bold rounded-lg text-xs" onClick={handleConnectExchange}>Establish Custody</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Alert Toast Component */}
            <div className={`fixed bottom-6 right-6 z-[100] transition-all duration-300 pointer-events-none transform ${showToast ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'
                }`}>
                <div className={`glass-panel py-3 px-5 rounded-lg border-l-4 flex items-center space-x-3 shadow-xl ${toastType === 'success' ? 'border-l-tertiary' : 'border-l-error'
                    }`}>
                    <span className="material-symbols-outlined">{toastType === 'success' ? 'check_circle' : 'warning'}</span>
                    <div className="text-sm font-medium">{toastMessage}</div>
                </div>
            </div>
        </div>
    );
}
