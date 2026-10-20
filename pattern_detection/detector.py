import pandas as pd
import numpy as np
from typing import List, Dict, Any

class PatternDetector:
    """
    Scans candlestick Series to detect standard trading patterns and breakouts.
    """
    
    @classmethod
    def detect_all(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        if len(df) < 5:
            return patterns
            
        # Detect single-bar/multi-bar candlestick patterns
        patterns.extend(cls.detect_doji(df))
        patterns.extend(cls.detect_hammer(df))
        patterns.extend(cls.detect_engulfing(df))
        patterns.extend(cls.detect_stars(df))
        
        # Detect macro structure patterns (requires more data)
        if len(df) >= 30:
            patterns.extend(cls.detect_double_tops_bottoms(df))
            patterns.extend(cls.detect_head_shoulders(df))
            patterns.extend(cls.detect_triangles_wedges(df))
            
        return patterns

    @classmethod
    def detect_doji(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        high = df['high'].values
        low = df['low'].values
        open_val = df['open'].values
        close = df['close'].values
        
        for i in range(len(df)):
            body = abs(close[i] - open_val[i])
            hl_range = high[i] - low[i]
            
            if hl_range > 0 and body / hl_range <= 0.1: # body is less than 10% of total bar range
                patterns.append({
                    "name": "Doji",
                    "index": i,
                    "time": int(df.index[i]) if isinstance(df.index[i], (int, np.integer)) else str(df.index[i]),
                    "confidence": 80,
                    "details": "Indicates market indecision. Keep watch on breakouts."
                })
        return patterns

    @classmethod
    def detect_hammer(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        high = df['high'].values
        low = df['low'].values
        open_val = df['open'].values
        close = df['close'].values
        
        for i in range(len(df)):
            body = abs(close[i] - open_val[i])
            hl_range = high[i] - low[i]
            if hl_range == 0:
                continue
                
            upper_shadow = high[i] - max(open_val[i], close[i])
            lower_shadow = min(open_val[i], close[i]) - low[i]
            
            # Lower shadow is at least twice the body size, upper shadow is small
            if lower_shadow >= 2 * body and upper_shadow / hl_range <= 0.1:
                patterns.append({
                    "name": "Hammer",
                    "index": i,
                    "time": int(df.index[i]) if isinstance(df.index[i], (int, np.integer)) else str(df.index[i]),
                    "confidence": 85,
                    "details": "Bullish reversal signal. Found support at lower levels."
                })
        return patterns

    @classmethod
    def detect_engulfing(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        open_val = df['open'].values
        close = df['close'].values
        
        for i in range(1, len(df)):
            prev_body = close[i-1] - open_val[i-1]
            curr_body = close[i] - open_val[i]
            
            # Prev body is small, current body completely covers it and direction is opposite
            if abs(prev_body) > 0 and abs(curr_body) > abs(prev_body):
                if prev_body < 0 and curr_body > 0 and open_val[i] <= close[i-1] and close[i] >= open_val[i-1]:
                    patterns.append({
                        "name": "Bullish Engulfing",
                        "index": i,
                        "time": int(df.index[i]) if isinstance(df.index[i], (int, np.integer)) else str(df.index[i]),
                        "confidence": 90,
                        "details": "Strong buyer pressure. Reversing bearish momentum."
                    })
                elif prev_body > 0 and curr_body < 0 and open_val[i] >= close[i-1] and close[i] <= open_val[i-1]:
                    patterns.append({
                        "name": "Bearish Engulfing",
                        "index": i,
                        "time": int(df.index[i]) if isinstance(df.index[i], (int, np.integer)) else str(df.index[i]),
                        "confidence": 90,
                        "details": "Strong seller pressure. Reversing bullish momentum."
                    })
        return patterns

    @classmethod
    def detect_stars(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        open_val = df['open'].values
        close = df['close'].values
        
        for i in range(2, len(df)):
            b1 = close[i-2] - open_val[i-2]
            b2 = close[i-1] - open_val[i-1]
            b3 = close[i] - open_val[i]
            
            # Morning Star: Large bearish candle -> Small indecisive gap candle -> Large bullish candle
            if b1 < 0 and abs(b2) < abs(b1)*0.25 and b3 > 0 and close[i] > (open_val[i-2] + close[i-2])/2:
                patterns.append({
                    "name": "Morning Star",
                    "index": i,
                    "time": int(df.index[i]) if isinstance(df.index[i], (int, np.integer)) else str(df.index[i]),
                    "confidence": 92,
                    "details": "Bullish reversal confirmation. Market indecision resolved upwards."
                })
            # Evening Star: Large bullish candle -> Small indecisive gap candle -> Large bearish candle
            elif b1 > 0 and abs(b2) < abs(b1)*0.25 and b3 < 0 and close[i] < (open_val[i-2] + close[i-2])/2:
                patterns.append({
                    "name": "Evening Star",
                    "index": i,
                    "time": int(df.index[i]) if isinstance(df.index[i], (int, np.integer)) else str(df.index[i]),
                    "confidence": 92,
                    "details": "Bearish reversal confirmation. Seller pressure resuming."
                })
        return patterns

    @classmethod
    def detect_double_tops_bottoms(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        high = df['high'].values
        low = df['low'].values
        
        # Simple rolling peak detection
        # Double Top: two peaks at a similar price level with a valley in between
        for i in range(15, len(df) - 5):
            window = high[i-15:i+5]
            # Simple peak locator
            peaks = []
            for j in range(2, len(window)-2):
                if window[j] == max(window[j-2:j+3]):
                    peaks.append(j)
                    
            if len(peaks) >= 2:
                p1_idx = i - 15 + peaks[0]
                p2_idx = i - 15 + peaks[-1]
                p1_val = high[p1_idx]
                p2_val = high[p2_idx]
                
                # Check price tolerance (diff <= 1.5%)
                if abs(p1_val - p2_val) / p1_val < 0.015 and (p2_idx - p1_idx) > 5:
                    patterns.append({
                        "name": "Double Top",
                        "start_index": p1_idx,
                        "end_index": p2_idx,
                        "confidence": 75,
                        "details": f"Resisted twice at critical level near ${p1_val:.2f}. Potential distribution."
                    })
                    
            # Double Bottom
            low_window = low[i-15:i+5]
            valleys = []
            for j in range(2, len(low_window)-2):
                if low_window[j] == min(low_window[j-2:j+3]):
                    valleys.append(j)
                    
            if len(valleys) >= 2:
                v1_idx = i - 15 + valleys[0]
                v2_idx = i - 15 + valleys[-1]
                v1_val = low[v1_idx]
                v2_val = low[v2_idx]
                
                if abs(v1_val - v2_val) / v1_val < 0.015 and (v2_idx - v1_idx) > 5:
                    patterns.append({
                        "name": "Double Bottom",
                        "start_index": v1_idx,
                        "end_index": v2_idx,
                        "confidence": 78,
                        "details": f"Established support floor twice near ${v1_val:.2f}. Accumulation signal."
                    })
                    
        return patterns

    @classmethod
    def detect_head_shoulders(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        # Head & Shoulders requires identifying three peaks: Left Shoulder, Head (highest), and Right Shoulder
        # We search in moving blocks of 30 bars
        high = df['high'].values
        for i in range(25, len(df) - 5):
            block = high[i-25:i+5]
            peaks = []
            for j in range(2, len(block)-2):
                if block[j] == max(block[j-2:j+3]):
                    peaks.append(j)
            
            if len(peaks) >= 3:
                p1_idx = i - 25 + peaks[0]
                p2_idx = i - 25 + peaks[1]
                p3_idx = i - 25 + peaks[2]
                
                h1 = high[p1_idx]
                h2 = high[p2_idx]
                h3 = high[p3_idx]
                
                # Head must be higher than both shoulders, shoulders should be roughly equal (diff <= 3%)
                if h2 > h1 and h2 > h3 and abs(h1 - h3)/h1 < 0.03:
                    patterns.append({
                        "name": "Head & Shoulders",
                        "start_index": p1_idx,
                        "end_index": p3_idx,
                        "confidence": 72,
                        "details": f"Head peak at ${h2:.2f} flanked by shoulders at ${h1:.2f}. Bearish reversal pattern."
                    })
        return patterns

    @classmethod
    def detect_triangles_wedges(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        # Triangle/Wedges are indicated by converging high-low trendlines
        # We can perform a linear regression on rolling peaks/valleys
        high = df['high'].values
        low = df['low'].values
        
        # Simple convergence test on the last 20 bars
        if len(df) >= 20:
            h_slope = np.polyfit(np.arange(20), np.asarray(high[-20:], dtype=float), 1)[0]
            l_slope = np.polyfit(np.arange(20), np.asarray(low[-20:], dtype=float), 1)[0]
            
            # converging lines
            if h_slope < 0 and l_slope > 0:
                patterns.append({
                    "name": "Symmetrical Triangle",
                    "start_index": len(df)-20,
                    "end_index": len(df)-1,
                    "confidence": 70,
                    "details": "Converging trendlines indicate consolidation. Watch out for high-volatility breakouts."
                })
            # Ascending triangle (flat top, rising lows)
            elif abs(h_slope) < 0.001 and l_slope > 0:
                patterns.append({
                    "name": "Ascending Triangle",
                    "start_index": len(df)-20,
                    "end_index": len(df)-1,
                    "confidence": 75,
                    "details": "Flat resistance and rising lows. Historically breakout is bullish."
                })
            # Descending triangle (flat bottom, falling highs)
            elif h_slope < 0 and abs(l_slope) < 0.001:
                patterns.append({
                    "name": "Descending Triangle",
                    "start_index": len(df)-20,
                    "end_index": len(df)-1,
                    "confidence": 75,
                    "details": "Flat support floor and lower highs. Historically breakout is bearish."
                })
                
        return patterns
