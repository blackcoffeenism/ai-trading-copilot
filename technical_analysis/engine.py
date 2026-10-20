import pandas as pd
import numpy as np
from typing import Dict, Any

class TechnicalAnalysisEngine:
    """
    Core mathematical engine to calculate technical analysis indicators.
    Takes a pandas DataFrame with ['open', 'high', 'low', 'close', 'volume'] columns.
    """
    
    @staticmethod
    def validate_df(df: pd.DataFrame):
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"DataFrame must contain column: {col}")

    @classmethod
    def calculate_sma(cls, df: pd.DataFrame, period: int = 14) -> pd.Series:
        return pd.Series(df['close'].rolling(window=period).mean())

    @classmethod
    def calculate_ema(cls, df: pd.DataFrame, period: int = 14) -> pd.Series:
        return pd.Series(df['close'].ewm(span=period, adjust=False).mean())

    @classmethod
    def calculate_rsi(cls, df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return pd.Series(rsi)

    @classmethod
    def calculate_macd(cls, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        ema_fast = cls.calculate_ema(df, fast)
        ema_slow = cls.calculate_ema(df, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }

    @classmethod
    def calculate_vwap(cls, df: pd.DataFrame) -> pd.Series:
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        tp_v = typical_price * df['volume']
        cumulative_tp_v = tp_v.cumsum()
        cumulative_volume = df['volume'].cumsum()
        return cumulative_tp_v / (cumulative_volume + 1e-9)

    @classmethod
    def calculate_atr(cls, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return pd.Series(atr)

    @classmethod
    def calculate_adx(cls, df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        upmove = df['high'] - df['high'].shift()
        downmove = df['low'].shift() - df['low']
        
        plus_dm = np.where((upmove > downmove) & (upmove > 0), upmove, 0)
        minus_dm = np.where((downmove > upmove) & (downmove > 0), downmove, 0)
        
        atr = cls.calculate_atr(df, period)
        
        plus_di = pd.Series(100 * (pd.Series(plus_dm).rolling(window=period).mean() / (atr + 1e-9)))
        minus_di = pd.Series(100 * (pd.Series(minus_dm).rolling(window=period).mean() / (atr + 1e-9)))
        
        dx = pd.Series(100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9))
        adx = pd.Series(dx.rolling(window=period).mean())
        
        return {
            "adx": adx,
            "plus_di": plus_di,
            "minus_di": minus_di
        }

    @classmethod
    def calculate_bollinger_bands(cls, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        sma = cls.calculate_sma(df, period)
        rstd = df['close'].rolling(window=period).std()
        
        upper_band = sma + (std_dev * rstd)
        lower_band = sma - (std_dev * rstd)
        
        return {
            "middle": sma,
            "upper": upper_band,
            "lower": lower_band
        }

    @classmethod
    def calculate_ichimoku(
        cls, df: pd.DataFrame, conversion: int = 9, base: int = 26, span_b: int = 52, lagging: int = 26
    ) -> Dict[str, Any]:
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        tenkan_sen = (df['high'].rolling(window=conversion).max() + df['low'].rolling(window=conversion).min()) / 2
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        kijun_sen = (df['high'].rolling(window=base).max() + df['low'].rolling(window=base).min()) / 2
        
        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(lagging)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        senkou_span_b = ((df['high'].rolling(window=span_b).max() + df['low'].rolling(window=span_b).min()) / 2).shift(lagging)
        
        # Chikou Span (Lagging Span): Close plotted 26 days behind
        chikou_span = df['close'].shift(-lagging)
        
        return {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_span_a": senkou_span_a,
            "senkou_span_b": senkou_span_b,
            "chikou_span": chikou_span
        }

    @classmethod
    def calculate_stochastic(cls, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        k_line = 100 * ((df['close'] - low_min) / (high_max - low_min + 1e-9))
        d_line = k_line.rolling(window=d_period).mean()
        
        return {
            "percent_k": k_line,
            "percent_d": d_line
        }

    @classmethod
    def calculate_cci(cls, df: pd.DataFrame, period: int = 20) -> pd.Series:
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(window=period).mean()
        # Mean Absolute Deviation
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        cci = (tp - sma_tp) / (0.015 * mad + 1e-9)
        return cci

    @classmethod
    def calculate_obv(cls, df: pd.DataFrame) -> pd.Series:
        obv = [0]
        close = df['close'].values
        volume = df['volume'].values
        
        for i in range(1, len(df)):
            if close[i] > close[i-1]:
                obv.append(obv[-1] + volume[i])
            elif close[i] < close[i-1]:
                obv.append(obv[-1] - volume[i])
            else:
                obv.append(obv[-1])
                
        return pd.Series(obv, index=df.index)

    @classmethod
    def calculate_mfi(cls, df: pd.DataFrame, period: int = 14) -> pd.Series:
        tp = (df['high'] + df['low'] + df['close']) / 3
        raw_money_flow = tp * df['volume']
        
        diff = tp.diff()
        pos_flow = np.where(diff > 0, raw_money_flow, 0)
        neg_flow = np.where(diff < 0, raw_money_flow, 0)
        
        pos_mf = pd.Series(pos_flow).rolling(window=period).sum()
        neg_mf = pd.Series(neg_flow).rolling(window=period).sum()
        
        m_ratio = pos_mf / (neg_mf + 1e-9)
        mfi = 100 - (100 / (1 + m_ratio))
        return pd.Series(np.asarray(mfi), index=df.index)

    @classmethod
    def calculate_supertrend(cls, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Dict[str, Any]:
        atr = cls.calculate_atr(df, period)
        hl2 = (df['high'] + df['low']) / 2

        basic_upperband = (hl2 + multiplier * atr).values
        basic_lowerband = (hl2 - multiplier * atr).values

        n = len(df)
        final_upperband = np.zeros(n)
        final_lowerband = np.zeros(n)
        supertrend_arr = np.zeros(n)
        direction_arr = np.ones(n, dtype=int)

        close = df['close'].values

        for i in range(1, n):
            # Upper band logic
            if basic_upperband[i] < final_upperband[i - 1] or close[i - 1] > final_upperband[i - 1]:
                final_upperband[i] = basic_upperband[i]
            else:
                final_upperband[i] = final_upperband[i - 1]

            # Lower band logic
            if basic_lowerband[i] > final_lowerband[i - 1] or close[i - 1] < final_lowerband[i - 1]:
                final_lowerband[i] = basic_lowerband[i]
            else:
                final_lowerband[i] = final_lowerband[i - 1]

            # Trend direction
            if supertrend_arr[i - 1] == final_upperband[i - 1]:
                direction_arr[i] = -1 if close[i] <= final_upperband[i] else 1
            else:
                direction_arr[i] = 1 if close[i] >= final_lowerband[i] else -1

            supertrend_arr[i] = final_lowerband[i] if direction_arr[i] == 1 else final_upperband[i]

        return {
            "supertrend": pd.Series(supertrend_arr, index=df.index),
            "direction": pd.Series(direction_arr, index=df.index),
        }

    @classmethod
    def calculate_donchian_channels(cls, df: pd.DataFrame, period: int = 20) -> Dict[str, Any]:
        upper = df['high'].rolling(window=period).max()
        lower = df['low'].rolling(window=period).min()
        middle = (upper + lower) / 2
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }

    @classmethod
    def calculate_keltner_channels(
        cls, df: pd.DataFrame, period: int = 20, atr_period: int = 10, multiplier: float = 2.0
    ) -> Dict[str, pd.Series]:
        ema = cls.calculate_ema(df, period)
        atr = cls.calculate_atr(df, atr_period)
        
        upper = ema + (multiplier * atr)
        lower = ema - (multiplier * atr)
        
        return {
            "upper": upper,
            "middle": ema,
            "lower": lower
        }

    @classmethod
    def calculate_pivot_points(cls, df: pd.DataFrame) -> Dict[str, pd.Series]:
        # Classic Daily Pivot point calculations
        # Pivot = (High + Low + Close) / 3
        # R1 = (2 * Pivot) - Low
        # S1 = (2 * Pivot) - High
        # R2 = Pivot + (High - Low)
        # S2 = Pivot - (High - Low)
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        return {
            "pivot": pivot,
            "r1": r1,
            "s1": s1,
            "r2": r2,
            "s2": s2
        }

    @classmethod
    def calculate_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Helper to append all indicators to the main DataFrame."""
        cls.validate_df(df)
        out = df.copy()
        
        out['sma_14'] = cls.calculate_sma(out, 14)
        out['ema_14'] = cls.calculate_ema(out, 14)
        out['rsi_14'] = cls.calculate_rsi(out, 14)
        
        macd = cls.calculate_macd(out)
        out['macd'] = macd['macd']
        out['macd_signal'] = macd['signal']
        out['macd_hist'] = macd['histogram']
        
        out['vwap'] = cls.calculate_vwap(out)
        out['atr_14'] = cls.calculate_atr(out, 14)
        
        adx = cls.calculate_adx(out)
        out['adx'] = adx['adx']
        out['plus_di'] = adx['plus_di']
        out['minus_di'] = adx['minus_di']
        
        bb = cls.calculate_bollinger_bands(out)
        out['bb_middle'] = bb['middle']
        out['bb_upper'] = bb['upper']
        out['bb_lower'] = bb['lower']
        
        stoch = cls.calculate_stochastic(out)
        out['stoch_k'] = stoch['percent_k']
        out['stoch_d'] = stoch['percent_d']
        
        out['cci_20'] = cls.calculate_cci(out, 20)
        out['obv'] = cls.calculate_obv(out)
        out['mfi_14'] = cls.calculate_mfi(out, 14)
        
        st = cls.calculate_supertrend(out)
        out['supertrend'] = st['supertrend']
        out['supertrend_direction'] = st['direction']
        
        donch = cls.calculate_donchian_channels(out)
        out['donch_upper'] = donch['upper']
        out['donch_middle'] = donch['middle']
        out['donch_lower'] = donch['lower']
        
        kelt = cls.calculate_keltner_channels(out)
        out['kelt_upper'] = kelt['upper']
        out['kelt_middle'] = kelt['middle']
        out['kelt_lower'] = kelt['lower']
        
        pivots = cls.calculate_pivot_points(out)
        out['pivot'] = pivots['pivot']
        out['pivot_r1'] = pivots['r1']
        out['pivot_s1'] = pivots['s1']
        out['pivot_r2'] = pivots['r2']
        out['pivot_s2'] = pivots['s2']
        
        return out
