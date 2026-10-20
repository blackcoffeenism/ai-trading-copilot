import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts';
import { API_BASE_URL } from '../config';

interface TradingChartProps {
    symbol: string;
    timeframe: string;
    showMA: boolean;
    showForecast: boolean;
    showPatterns: boolean;
    theme: 'light' | 'dark';
}

export const TradingChart: React.FC<TradingChartProps> = ({
    symbol,
    timeframe,
    showMA,
    showForecast,
    showPatterns,
    theme
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
    const ema7SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
    const ma25SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
    const sarSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
    const forecastSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

    // Generate mock historical and forecast data
    const generateChartData = (sym: string, tf: string) => {
        const dataCount = tf === '1H' ? 100 : tf === '4H' ? 150 : 200;
        const prices: CandlestickData[] = [];
        
        let currentPrice = 100.00;
        if (sym === 'BTC') currentPrice = 64230.50;
        else if (sym === 'ETH') currentPrice = 3450.20;
        else if (sym === 'SOL') currentPrice = 145.80;
        else if (sym === 'XRP') currentPrice = 0.5824;
        else if (sym === 'ADA') currentPrice = 0.3850;
        else if (sym === 'Nvidia') currentPrice = 109.20;
        else if (sym === 'AAPL') currentPrice = 218.40;
        else if (sym === 'TSLA') currentPrice = 172.50;
        else if (sym === 'MSFT') currentPrice = 420.50;
        else if (sym === 'AMZN') currentPrice = 184.20;
        else if (sym === 'GOOGL') currentPrice = 173.80;
        else if (sym === 'EUR') currentPrice = 1.0824;
        else if (sym === 'GBP') currentPrice = 1.2745;
        else if (sym === 'JPY') currentPrice = 153.25;
        else if (sym === 'AUD') currentPrice = 0.6542;
        else if (sym === 'Gold') currentPrice = 2445.80;
        else if (sym === 'Crude Oil') currentPrice = 78.42;
        else if (sym === 'Silver') currentPrice = 28.15;
        else if (sym === 'S&P 500') currentPrice = 5410.25;
        else if (sym === 'Nasdaq 100') currentPrice = 19120.50;
        else if (sym === 'Dow Jones') currentPrice = 39680.15;
        else if (sym === 'JFC') currentPrice = 260.50;
        else if (sym === 'ALI') currentPrice = 29.80;
        else if (sym === 'BDO') currentPrice = 145.20;
        else if (sym === 'SM') currentPrice = 880.00;
        else if (sym === 'TEL') currentPrice = 1350.00;
        const interval = tf === '1H' ? 3600 : tf === '4H' ? 14400 : 86400;
        let time = Math.floor(Date.now() / 1000) - (dataCount * interval);

        // Generate history
        for (let i = 0; i < dataCount; i++) {
            const volatility = sym === 'EUR' ? 0.002 : 0.015;
            const change = currentPrice * (Math.random() - 0.49) * volatility;
            const open = currentPrice;
            const close = currentPrice + change;
            const high = Math.max(open, close) + (Math.random() * (currentPrice * 0.003));
            const low = Math.min(open, close) - (Math.random() * (currentPrice * 0.003));

            prices.push({
                time: (time + (i * interval)) as any,
                open,
                high,
                low,
                close
            });
            currentPrice = close;
        }
        return prices;
    };

    useEffect(() => {
        if (!containerRef.current) return;

        const isDark = theme === 'dark';
        
        // 1. Initialize Chart
        const chart = createChart(containerRef.current, {
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight || 400,
            layout: {
                background: { type: ColorType.Solid, color: isDark ? '#111417' : '#ffffff' },
                textColor: isDark ? '#c2c6d8' : '#333333',
            },
            grid: {
                vertLines: { color: isDark ? '#1d2023' : '#f0f0f0' },
                horzLines: { color: isDark ? '#1d2023' : '#f0f0f0' },
            },
            crosshair: {
                mode: 0,
            },
            rightPriceScale: {
                borderColor: isDark ? '#2B3139' : '#e0e0e0',
            },
            timeScale: {
                borderColor: isDark ? '#2B3139' : '#e0e0e0',
                timeVisible: true,
            },
        });

        // 2. Add Candlestick Series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#3be194',
            downColor: '#ffb4ab',
            borderDownColor: '#ffb4ab',
            borderUpColor: '#3be194',
            wickDownColor: '#ffb4ab',
            wickUpColor: '#3be194',
        });

        // 3. Add Line Series for indicators
        const ema7Series = chart.addLineSeries({
            color: '#7701d0',
            lineWidth: 2,
            title: 'EMA 7'
        });

        const ma25Series = chart.addLineSeries({
            color: '#b3c5ff',
            lineWidth: 2,
            title: 'MA 25'
        });

        const sarSeries = chart.addLineSeries({
            color: '#ff9800',
            lineWidth: 2,
            lineStyle: 1, // Dotted
            title: 'SAR'
        });

        // 4. Add Dotted Line Series for Chronos Forecast
        const forecastSeries = chart.addLineSeries({
            color: '#00e5ff',
            lineWidth: 2,
            lineStyle: 2, // Dotted
            title: 'Chronos Forecast'
        });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        ema7SeriesRef.current = ema7Series;
        ma25SeriesRef.current = ma25Series;
        sarSeriesRef.current = sarSeries;
        forecastSeriesRef.current = forecastSeries;

        // 5. Load and Set Data
        let tickIntervalId: any = null;

        const loadChartData = async () => {
            let data: CandlestickData[] = [];
            try {
                const response = await fetch(`${API_BASE_URL}/history?symbol=${symbol}&timeframe=${timeframe}`);
                if (response.ok) {
                    const json = await response.json();
                    if (Array.isArray(json) && json.length > 0) {
                        data = json;
                    }
                }
            } catch (err) {
                console.warn("FastAPI backend history fetch refused. Falling back to mock generator.", err);
            }

            if (data.length === 0) {
                data = generateChartData(symbol, timeframe);
            }

            candleSeries.setData(data);

            // 6. Handle Indicators calculations (EMA 7, MA 25, SAR)
            let lastEma7Val = data[0].close;
            const emaMultiplier = 2 / (7 + 1); // 0.25

            let isUptrend = true;
            let sarVal = (data[0] as any).low;
            let epVal = (data[0] as any).high;
            let afVal = 0.02;
            const afStep = 0.02;
            const afMax = 0.20;

            if (showMA) {
                const ema7Data = [];
                const ma25Data = [];
                const sarData = [];

                for (let i = 0; i < data.length; i++) {
                    const close = (data[i] as any).close;
                    
                    // EMA 7 Calculation
                    if (i === 0) {
                        lastEma7Val = close;
                    } else {
                        lastEma7Val = close * emaMultiplier + lastEma7Val * (1 - emaMultiplier);
                    }
                    
                    if (i >= 6) {
                        ema7Data.push({ time: data[i].time, value: lastEma7Val });
                    }

                    // SAR Calculation
                    if (i === 0) {
                        sarData.push({ time: data[i].time, value: sarVal });
                    } else {
                        const currBar = data[i] as any;
                        let nextSar = sarVal + afVal * (epVal - sarVal);

                        if (isUptrend) {
                            if (i >= 2) {
                                const low1 = (data[i - 1] as any).low;
                                const low2 = (data[i - 2] as any).low;
                                nextSar = Math.min(nextSar, low1, low2);
                            }
                            if (currBar.low < nextSar) {
                                isUptrend = false;
                                nextSar = epVal;
                                epVal = currBar.low;
                                afVal = 0.02;
                            } else {
                                if (currBar.high > epVal) {
                                    epVal = currBar.high;
                                    afVal = Math.min(afMax, afVal + afStep);
                                }
                            }
                        } else {
                            if (i >= 2) {
                                const high1 = (data[i - 1] as any).high;
                                const high2 = (data[i - 2] as any).high;
                                nextSar = Math.max(nextSar, high1, high2);
                            }
                            if (currBar.high > nextSar) {
                                isUptrend = true;
                                nextSar = epVal;
                                epVal = currBar.high;
                                afVal = 0.02;
                            } else {
                                if (currBar.low < epVal) {
                                    epVal = currBar.low;
                                    afVal = Math.min(afMax, afVal + afStep);
                                }
                            }
                        }
                        sarVal = nextSar;
                        sarData.push({ time: currBar.time, value: sarVal });
                    }

                    // MA 25 Calculation
                    if (i >= 24) {
                        let sum = 0;
                        for (let j = 0; j < 25; j++) sum += (data[i - j] as any).close;
                        ma25Data.push({ time: data[i].time, value: sum / 25 });
                    }
                }

                ema7Series.setData(ema7Data);
                ma25Series.setData(ma25Data);
                sarSeries.setData(sarData);
            }

            // 7. Handle Forecast Projections
            if (showForecast) {
                const forecastData = [];
                const lastBar = data[data.length - 1];
                let lastClose = (lastBar as any).close;
                const interval = timeframe === '1H' ? 3600 : timeframe === '4H' ? 14400 : 86400;
                
                // Connect forecast line to last historical candle
                forecastData.push({ time: lastBar.time, value: lastClose });
                
                for (let i = 1; i <= 10; i++) {
                    lastClose += lastClose * (Math.random() - 0.47) * 0.01;
                    forecastData.push({
                        time: ((lastBar.time as any) + (i * interval)) as any,
                        value: lastClose
                    });
                }
                forecastSeries.setData(forecastData);
            }

            // 8. Handle Patterns Markers
            if (showPatterns && data.length > 30) {
                const markers = [];
                if (data[100]) {
                    markers.push({
                        time: data[100].time,
                        position: 'aboveBar' as const,
                        color: '#e1e2e7',
                        shape: 'arrowDown' as const,
                        text: 'Doji (Indecision)'
                    });
                }
                if (data[150]) {
                    markers.push({
                        time: data[150].time,
                        position: 'belowBar' as const,
                        color: '#3be194',
                        shape: 'arrowUp' as const,
                        text: 'Bullish Engulfing'
                    });
                }
                candleSeries.setMarkers(markers);
            }

            chart.timeScale().fitContent();

            // 9. Real-time ticking simulation
            let lastBar = { ...data[data.length - 1] };
            tickIntervalId = setInterval(() => {
                const volatility = symbol === 'EUR' ? 0.0005 : 0.002;
                const changePercent = (Math.random() - 0.495) * volatility;
                const change = lastBar.close * changePercent;
                const newClose = lastBar.close + change;

                lastBar = {
                    ...lastBar,
                    close: newClose,
                    high: Math.max(lastBar.high, newClose),
                    low: Math.min(lastBar.low, newClose)
                };

                // Update the candlestick
                candleSeries.update(lastBar as any);

                // Update the indicators for the ticking bar
                if (showMA && data.length > 25) {
                    // Update EMA 7
                    lastEma7Val = lastBar.close * emaMultiplier + lastEma7Val * (1 - emaMultiplier);
                    ema7Series.update({ time: lastBar.time, value: lastEma7Val });

                    // Update MA 25
                    let sum25 = 0;
                    for (let j = 1; j < 25; j++) {
                        sum25 += (data[data.length - 1 - j] as any).close;
                    }
                    sum25 += lastBar.close;
                    ma25Series.update({ time: lastBar.time, value: sum25 / 25 });

                    // Update SAR
                    let tickingSar = sarVal + afVal * (epVal - sarVal);
                    if (isUptrend) {
                        const low1 = (data[data.length - 1] as any).low;
                        const low2 = (data[data.length - 2] as any).low;
                        tickingSar = Math.min(tickingSar, low1, low2);

                        if (lastBar.close < tickingSar) {
                            isUptrend = false;
                            tickingSar = epVal;
                            epVal = lastBar.low;
                            afVal = 0.02;
                        } else {
                            if (lastBar.high > epVal) {
                                epVal = lastBar.high;
                                afVal = Math.min(afMax, afVal + afStep);
                            }
                        }
                    } else {
                        const high1 = (data[data.length - 1] as any).high;
                        const high2 = (data[data.length - 2] as any).high;
                        tickingSar = Math.max(tickingSar, high1, high2);

                        if (lastBar.close > tickingSar) {
                            isUptrend = true;
                            tickingSar = epVal;
                            epVal = lastBar.high;
                            afVal = 0.02;
                        } else {
                            if (lastBar.low < epVal) {
                                epVal = lastBar.low;
                                afVal = Math.min(afMax, afVal + afStep);
                            }
                        }
                    }
                    sarVal = tickingSar;
                    sarSeries.update({ time: lastBar.time, value: sarVal });
                }
            }, 1000);
        };

        loadChartData();

        // 10. Resize Observer handler
        const resizeObserver = new ResizeObserver((entries) => {
            if (entries.length === 0 || !chartRef.current) return;
            const { width, height } = entries[0].contentRect;
            chartRef.current.resize(width, height);
        });
        resizeObserver.observe(containerRef.current);

        return () => {
            if (tickIntervalId) clearInterval(tickIntervalId);
            resizeObserver.disconnect();
            chart.remove();
            chartRef.current = null;
        };
    }, [symbol, timeframe, showMA, showForecast, showPatterns, theme]);

    return (
        <div className="w-full h-full min-h-[380px] relative">
            <div ref={containerRef} className="w-full h-full absolute inset-0" />
        </div>
    );
};
