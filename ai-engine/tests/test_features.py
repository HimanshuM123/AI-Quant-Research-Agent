import numpy as np
import pandas as pd

from src.quant.features import add_quant_features


def test_quant_features_calculate_returns_and_momentum():
    index = pd.date_range("2025-01-01", periods=60, freq="D")
    close = np.arange(100.0, 160.0)
    frame = pd.DataFrame(
        {
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": 1000,
        },
        index=index,
    )

    result = add_quant_features(frame, volatility_window=20, momentum_window=20)

    expected_simple_return = 159.0 / 158.0 - 1.0
    expected_momentum = 159.0 / 139.0 - 1.0

    assert np.isclose(result.iloc[-1]["simple_return"], expected_simple_return)
    assert np.isclose(result.iloc[-1]["momentum"], expected_momentum)
    assert not pd.isna(result.iloc[-1]["sma_20"])
    assert not pd.isna(result.iloc[-1]["sma_50"])
