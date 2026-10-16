# Hang Seng Index (HSI) Next-Day Quantitative ML Forecasting System

A fully automated, leakage-free quantitative machine learning pipeline that forecasts next-trading-day closing level, direction, and heavy-tailed uncertainty intervals for the Hang Seng Index (^HSI).

### Architecture
- **Features:** 34 cross-asset features (US risk transmission, Asian indices, FX peg, commodities, calendar encodings).
- **Ensemble:** LightGBM Regressor + XGBoost Regressor + ElasticNet (Equal-weighted).
- **Uncertainty Bounds:** Student-t conditional dispersion with 80% and 95% intervals.
- **Validation:** 1,340-day expanding walk-forward validation (59.63% directional hit ratio, +0.2735 IC).
- **Execution:** Zero-click live deployment via Streamlit.
