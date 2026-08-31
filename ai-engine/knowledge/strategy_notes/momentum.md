# Momentum and Trend-Following Research Notes

Momentum strategies test whether assets with positive past returns continue to outperform over a subsequent horizon. A simple medium-term equity implementation can use a trailing return feature together with a trend filter such as price above a moving average. Important failure modes include momentum crashes during sharp market reversals, crowded positioning, excessive turnover, and parameter overfitting. Robust evaluation should include transaction costs, out-of-sample testing, multiple assets, and walk-forward validation.
