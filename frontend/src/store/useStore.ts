import { create } from 'zustand';

export interface UserProfile {
    id: string;
    username: string;
    fullName: string;
    tier: 'free' | 'premium' | 'institutional';
    settings: {
        defaultLeverage: number;
        riskTolerance: 'conservative' | 'moderate' | 'aggressive';
        aiModel: string;
    };
}

export interface WatchlistSymbol {
    id: string;
    watchlistId: string;
    symbol: string;
    marketType: 'crypto' | 'stocks' | 'forex' | 'indices';
}

export interface Watchlist {
    id: string;
    name: string;
    isDefault: boolean;
    symbols: WatchlistSymbol[];
}

export interface PortfolioAsset {
    id: string;
    symbol: string;
    quantity: number;
    averageBuyPrice: number;
}

export interface Portfolio {
    id: string;
    name: string;
    availableUsd: number;
    assets: PortfolioAsset[];
}

export interface JournalEntry {
    id: string;
    symbol: string;
    entryPrice: number;
    exitPrice: number;
    quantity: number;
    side: 'BUY' | 'SELL' | 'LONG' | 'SHORT';
    emotion: string;
    outcome: 'PROFIT' | 'LOSS' | 'BREAKEAVEN';
    pnlValue: number;
    notes: string;
    aiFeedback?: string;
    createdAt: string;
}

export interface Alert {
    id: string;
    symbol: string;
    alertType: 'price_above' | 'price_below' | 'indicator' | 'pattern' | 'forecast';
    conditionValue: string;
    isActive: boolean;
    createdAt: string;
}

export interface NewsArticle {
    id: string;
    title: string;
    source: string;
    publishedAt: string;
    snippet: string;
    sentiment: 'Positive' | 'Negative' | 'Neutral';
    sentimentScore: number;
    marketImpact: 'High' | 'Medium' | 'Low';
}

interface AppState {
    currentView: string;
    theme: 'light' | 'dark';
    user: UserProfile | null;
    watchlists: Watchlist[];
    portfolios: Portfolio[];
    journalEntries: JournalEntry[];
    alerts: Alert[];
    news: NewsArticle[];
    selectedSymbol: string;
    timeframe: string;
    
    // Actions
    setView: (view: string) => void;
    toggleTheme: () => void;
    setUser: (user: UserProfile | null) => void;
    setWatchlists: (watchlists: Watchlist[]) => void;
    setPortfolios: (portfolios: Portfolio[]) => void;
    setJournalEntries: (entries: JournalEntry[]) => void;
    setAlerts: (alerts: Alert[]) => void;
    setNews: (news: NewsArticle[]) => void;
    setSelectedSymbol: (symbol: string) => void;
    setTimeframe: (tf: string) => void;
}

export const useStore = create<AppState>((set) => ({
    currentView: 'dashboard',
    theme: 'dark',
    user: {
        id: "00000000-0000-0000-0000-000000000000",
        username: "dev_trader",
        fullName: "Premium Account",
        tier: "premium",
        settings: {
            defaultLeverage: 1,
            riskTolerance: "moderate",
            aiModel: "Gemini 1.5 Pro"
        }
    },
    watchlists: [
        {
            id: "wl_1",
            name: "Core Assets",
            isDefault: true,
            symbols: [
                { id: "s1", watchlistId: "wl_1", symbol: "BTC", marketType: "crypto" },
                { id: "s2", watchlistId: "wl_1", symbol: "ETH", marketType: "crypto" },
                { id: "s3", watchlistId: "wl_1", symbol: "SOL", marketType: "crypto" }
            ]
        }
    ],
    portfolios: [
        {
            id: "p_1",
            name: "Mock Spot Portfolio",
            availableUsd: 50000.00,
            assets: [
                { id: "pa_1", symbol: "BTC", quantity: 1.15, averageBuyPrice: 62100.00 },
                { id: "pa_2", symbol: "ETH", quantity: 5.40, averageBuyPrice: 3250.00 }
            ]
        }
    ],
    journalEntries: [
        {
            id: "j_1",
            symbol: "BTC",
            entryPrice: 63980.00,
            exitPrice: 64230.50,
            quantity: 0.15,
            side: "BUY",
            emotion: "Disciplined",
            outcome: "PROFIT",
            pnlValue: 37.57,
            notes: "Executed based on EMA 7 crossover retest of hourly support. Risk sizing kept strictly under 2.5%.",
            aiFeedback: "AI FEEDBACK: Entry logged successfully. Trade on BTC (BUY) showed proper emotional grounding (Disciplined). Focus on executing strictly based on your SMA strategy.",
            createdAt: new Date().toISOString()
        }
    ],
    alerts: [
        {
            id: "a_1",
            symbol: "BTC",
            alertType: "price_above",
            conditionValue: "65000",
            isActive: true,
            createdAt: new Date().toISOString()
        }
    ],
    news: [
        { id: "n1", title: "Federal Reserve Signals Potential Rate Cut in Upcoming Meeting", source: "Bloomberg", publishedAt: "10m ago", snippet: "Fed chairman hints inflation indicators are cooling, raising expectations of rate relief next month.", sentiment: "Positive", sentimentScore: 88, marketImpact: "High" },
        { id: "n2", title: "SEC Approves In-Kind Creation Options for Cryptic Index Products", source: "Reuters", publishedAt: "35m ago", snippet: "New regulatory approvals clear path for major institutional capital deployment into derivative holdings.", sentiment: "Positive", sentimentScore: 94, marketImpact: "High" },
        { id: "n3", title: "MicroStrategy Acquires Additional 12,000 BTC for $780 Million", source: "CoinDesk", publishedAt: "1h ago", snippet: "Company continues treasury reserves consolidation, bringing total asset holding value beyond $14B.", sentiment: "Positive", sentimentScore: 91, marketImpact: "Medium" }
    ],
    selectedSymbol: 'BTC',
    timeframe: '1D',

    setView: (view) => set({ currentView: view }),
    toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
    setUser: (user) => set({ user }),
    setWatchlists: (watchlists) => set({ watchlists }),
    setPortfolios: (portfolios) => set({ portfolios }),
    setJournalEntries: (journalEntries) => set({ journalEntries }),
    setAlerts: (alerts) => set({ alerts }),
    setNews: (news) => set({ news }),
    setSelectedSymbol: (selectedSymbol) => set({ selectedSymbol }),
    setTimeframe: (timeframe) => set({ timeframe })
}));
