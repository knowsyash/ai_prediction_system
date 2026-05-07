# Next Month Predictive Modeling

## The Forecasting Engine
The final stage of the pipeline (`predict_next_month.py`) utilizes historic data combined with real-time sentiment to mathematically project future device ratings.

## Weighted Prediction Signals
The system forecasts the next-month average rating using an ensemble of three specialized signals:
1. **Linear Trend:** Analyzes the historical month-over-month trajectory of star ratings.
2. **Exponential Smoothing:** Accords heavier weight to the most recent weeks' data to rapidly respond to new sentiment shifts.
3. **Sentiment Signal:** Integrates the high-accuracy NLP scores derived from our Soft Voting ensemble model as a leading indicator of future performance.

## Visualization & Output
* The system dynamically configures weights for these three signals based on historical accuracy.
* The final output predicts the anticipated device rating (e.g., iPhone 15 predicting a 4.1 next month) and is saved directly to `next_month_prediction_v2.csv`.
* Time-series graphs (`trend_<device>_v2.png`) are automatically generated to visually map the historic trajectory against the predicted future drop or rise.