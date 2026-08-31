import numpy as np
import pandas as pd

TRADING_DAYS = 252


def add_quant_features(
    frame: pd.DataFrame,
    volatility_window: int = 20,
    momentum_window: int = 20,
) -> pd.DataFrame:
    """Add deterministic quantitative features to OHLCV data.

    Definitions
    -----------
    Simple return:
        R_t = P_t / P_{t-1} - 1

    Log return:
        r_t = ln(P_t / P_{t-1})

    Annualized rolling volatility:
        sigma_annual = std(r_t, ..., r_{t-N+1}) * sqrt(252)

    Momentum:
        M_t(N) = P_t / P_{t-N} - 1
    """
    if frame.empty:
        return frame.copy()

    df = frame.copy().sort_index()

    if "Close" not in df.columns:
        raise ValueError("Input frame must contain a Close column")

    close = pd.to_numeric(df["Close"], errors="coerce")

    df["simple_return"] = close.pct_change()
    df["log_return"] = np.log(close / close.shift(1))
    df["volatility"] = (
        df["log_return"].rolling(volatility_window).std(ddof=1)
        * np.sqrt(TRADING_DAYS)
    )
    df["momentum"] = close / close.shift(momentum_window) - 1.0
    df["sma_20"] = close.rolling(20).mean()
    df["sma_50"] = close.rolling(50).mean()

    return df
