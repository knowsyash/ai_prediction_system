
# In-Depth Technical Report: Predictive Modeling and Forecasting

**Version 3.0 - Last Updated: 2026-04-28**

## 1. The Apex of the Pipeline: From Analysis to Prediction

This is the final and most crucial stage of the AI Prediction System. All preceding work—scraping, cleaning, sentiment analysis, and ensembling—has been in service of this ultimate goal: to transform historical data and sentiment into a forward-looking, actionable prediction. The `5_next_month` folder, and specifically the `predict_next_month.py` script, represents the culmination of this entire effort.

The objective of this phase is to forecast the average customer rating for each smartphone for the *next month*. This is not a simple extrapolation; it is a sophisticated synthesis of multiple signals, each capturing a different aspect of the product's market trajectory.

This report will provide a deep, mathematical, and procedural dissection of the methodologies employed in the `predict_next_month.py` script.

---

## 2. The Multi-Signal Approach to Forecasting

The strength of the `predict_next_month.py` script lies in its refusal to rely on a single predictive method. Instead, it calculates three distinct predictive signals and then combines them in a weighted ensemble, creating a forecast that is more robust and reliable than any single signal alone.

### 2.1. Signal 1: Linear Trend Projection (The Long-Term View)

This signal is designed to capture the stable, long-term trajectory of a product's ratings.

#### **Internal Mechanics & Mathematical Foundation:**

1.  **Data Aggregation:** The process begins by loading the cleaned review data for a specific device (e.g., `iphone15.csv`) from the `2_dataset_final_folder`. It then groups all reviews by month and calculates the average (mean) star rating for each month. This creates a time series.
    *   **Example Time Series:** `[Month 1: 4.5, Month 2: 4.6, Month 3: 4.4, ...]`

2.  **Linear Regression:** The script then applies a linear regression model to this time series. The goal is to find the "line of best fit" that describes the relationship between time and the average rating. This is done by solving the classic linear equation:
    $$
    y = mx + c
    $$
    Where:
    *   $y$ is the `mean_rating` for a given month.
    *   $x$ is the time index (e.g., 0 for the first month, 1 for the second, and so on).
    *   $m$ is the **slope** of the line, representing the average rate of change in ratings per month.
    *   $c$ is the **intercept**, representing the starting rating at time 0.

    The `numpy.polyfit` function is used to find the optimal values for $m$ and $c$ that minimize the squared distance between the actual data points and the fitted line.

3.  **Extrapolation:** Once the slope ($m$) and intercept ($c$) are determined, the script forecasts the rating for the next month. If there are $N$ months of historical data (indexed 0 to $N-1$), the next month has an index of $N$. The prediction is calculated as:
    $$
    \text{Prediction} = m \times N + c
    $$

This signal provides a stable, long-term directional forecast, but it is not highly responsive to recent, sudden changes.

### 2.2. Signal 2: Exponential Smoothing (The Recent Momentum)

This signal is designed to capture the recent momentum of a product's ratings, giving more importance to the latest data.

#### **Internal Mechanics & Mathematical Foundation:**

1.  **Input Data:** This method also uses the same monthly average rating time series as the Linear Trend.

2.  **Exponential Smoothing Algorithm:** The script uses Single Exponential Smoothing. It works by calculating a "smoothed" value for each point in the time series. The forecast for the next period is simply the last smoothed value calculated. The core formula is:
    $$
    S_t = \alpha \times y_t + (1 - \alpha) \times S_{t-1}
    $$
    Where:
    *   $S_t$ is the smoothed value at the current time step $t$.
    *   $y_t$ is the actual observed `mean_rating` at time $t$.
    *   $S_{t-1}$ is the smoothed value from the *previous* time step.
    *   $\alpha$ is the **smoothing factor** (alpha). This is the most critical parameter.

3.  **The Smoothing Factor ($\alpha$):** The `alpha` value, set dynamically in the script, determines how much weight is given to recent observations.
    *   A **high alpha** (e.g., 0.8) means the model is very responsive to the latest data point and has little "memory" of past values.
    *   A **low alpha** (e.g., 0.1) means the model is very smooth and has a long memory, changing slowly.
    *   **In our script:** The alpha is set to **0.45** if there are fewer than 8 months of data, and **0.30** otherwise. This is a smart heuristic: with less data, we trust recent events more (higher alpha); with more data, we trust the longer-term smoothed trend more (lower alpha).

The final prediction from this signal is the last calculated smoothed value, $S_N$. This makes it highly effective at capturing recent spikes or dips in performance.

### 2.3. Signal 3: The Ensemble Sentiment Signal (The "Ground Truth" Mood)

This is the most sophisticated signal, acting as a leading indicator of customer sentiment.

#### **Which Ensemble Model Was Chosen?**

The `predict_next_month.py` script explicitly loads the results from the **Soft Voting** ensemble model. This choice is based on the results from the `4_enemble_analysis` stage, where Soft Voting was identified as the best all-around performer, achieving the highest **Macro F1-Score** and **Pearson Correlation**. It represents the most balanced and reliable sentiment predictor.

#### **Internal Mechanics:**

1.  **Load Best Model's Predictions:** The script loads `ensemble_results_v2.csv`. This file contains a row for every single review, including the `soft_vote_pred_rating`—a continuous score from 1 to 5 representing the Soft Voting model's prediction for that review.
2.  **Aggregate Recent Sentiment:** It filters these results to include only the reviews from the **most recent month** of data.
3.  **Calculate Average:** It then calculates the average (mean) of the `soft_vote_pred_rating` for all reviews in that last month.
4.  **Use as Forecast:** This single value—the average sentiment score from the best model on the most recent data—is used as the third predictive signal. It represents the most up-to-date "mood" of the market.

---

## 3. The Final Forecast: A Dynamic Weighted Ensemble

The final prediction is not a simple average. It is a weighted combination of the three signals, where the weights are **dynamically adjusted** based on the amount of historical data available for a device. This is a critical feature that makes the model adaptive.

#### **The Weighting Strategy:**

The weights are defined in the `predict_device` function in the script and can be seen in the output `next_month_prediction_v2.csv`.

*   **If Months of History < 3 (Very Little Data):**
    *   Linear Trend: **20%** (`w_linear` = 0.20)
    *   Exp. Smoothing: **30%** (`w_exp_smooth` = 0.30)
    *   Sentiment Signal: **50%** (`w_sentiment` = 0.50)
    *   **Reasoning:** With very little historical data, the time-series models are unreliable. The forecast therefore leans heavily on the most trustworthy signal: the immediate market mood captured by the advanced Sentiment Signal.

*   **If 3 <= Months of History < 6 (Some Data):**
    *   Linear Trend: **30%** (`w_linear` = 0.30)
    *   Exp. Smoothing: **35%** (`w_exp_smooth` = 0.35)
    *   Sentiment Signal: **35%** (`w_sentiment` = 0.35)
    *   **Reasoning:** With a few months of data, the time-series models start to become more reliable. The weights are now more balanced, giving roughly equal importance to the long-term trend, recent momentum, and current sentiment.

*   **If Months of History >= 6 (Sufficient Data):**
    *   Linear Trend: **40%** (`w_linear` = 0.40)
    *   Exp. Smoothing: **35%** (`w_exp_smooth` = 0.35)
    *   Sentiment Signal: **25%** (`w_sentiment` = 0.25)
    *   **Reasoning:** With a substantial amount of historical data, the Linear Trend becomes the most reliable indicator of the product's long-term trajectory. It is given the highest weight, while the Sentiment Signal's weight is reduced to prevent short-term volatility from overpowering the stable trend.

The final predicted rating is calculated as:
$$
\text{Final Prediction} = (w_1 \times \text{Linear}) + (w_2 \times \text{Exp. Smooth}) + (w_3 \times \text{Sentiment})
$$

This dynamic weighting strategy is a hallmark of a robust forecasting system, as it adapts its own logic based on the quality and quantity of the data it has to work with.

---

## 4. Proven Results: The Final Predictions

The tangible output of this entire project is captured in the `next_month_prediction_v2.csv` file. This file provides the concrete, data-driven forecast for the next month's average rating for each device.

### Next-Month Rating Forecast

| Device      | Target Month | Last Observed Rating | Linear Trend Forecast | Exp. Smoothing Forecast | Sentiment Signal Forecast | **Final Predicted Rating** |
|-------------|--------------|----------------------|-----------------------|-------------------------|---------------------------|--------------------------|
| **iPhone 16** | Feb 2026     | 4.455                | 4.530                 | 4.615                   | 4.160                     | **4.467**                |
| **iPhone 15** | Feb 2025     | 4.633                | 4.566                 | 4.618                   | 4.139                     | **4.477**                |
| **iQOO Z10**  | Mar 2026     | 4.643                | 4.606                 | 4.445                   | 4.005                     | **4.339**                |

### Analysis of the Forecast:

- **iPhone 16 Forecast (4.467):** With 14 months of history, this device uses the "Sufficient Data" weights (40/35/25). The strong positive momentum seen in the Linear Trend and Exponential Smoothing signals is correctly tempered by a more moderate recent Sentiment Signal, resulting in a stable forecast.

- **iPhone 15 Forecast (4.477):** With 17 months of history, this also uses the 40/35/25 weights. The system predicts a slight downward correction. While its last observed rating was very high (4.633), all three predictive signals point to a slightly lower, more sustainable rating.

- **iQOO Z10 Forecast (4.339):** With only 3 months of history, this device uses the "Some Data" weights (30/35/35). The model predicts a significant downward trend. The very low recent Sentiment Signal (4.005) carries significant weight, pulling the prediction down and suggesting a potential negative turn in market perception.

---

## 5. Data Sources and Outputs

### 5.1. Data Inputs
- **`2_dataset_final_folder/*.csv`:** Used to get the historical review dates and star ratings for calculating the time-series trends.
- **`4_enemble_analysis/ensemble_results_v2.csv`:** The source of the high-quality sentiment scores from the **Soft Voting** ensemble model.

### 5.2. Key Outputs
- **`next_month_prediction_v2.csv`:** The main output file, containing the final weighted forecast and all its component parts.
- **`trend_<device>_v2.png`:** Plots visualizing the historical trend and forecast for each device.
- **`prediction_summary_v2.png`:** A bar chart comparing the final predictions for all devices.
- **`component_breakdown_v2.png`:** A new plot showing the contribution of each of the three signals to the final forecast for each device.

---

## 6. Conclusion: Delivering Actionable Insight

The `5_next_month` stage successfully bridges the gap between historical data analysis and forward-looking prediction. By synthesizing multiple analytical signals using a dynamic, data-aware weighting strategy, the system delivers a clear, robust, and highly defensible forecast. The final prediction is not just a number; it is the culmination of a rigorous, multi-stage process of data acquisition, cleaning, analysis, and modeling.

