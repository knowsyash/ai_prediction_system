# Model Evaluation & Validation Methodology

## Ground Truth Setup
* **Benchmark:** Model predictions were directly validated against actual customer Star Ratings.
* **Why we used it:** Since star ratings are locked onto a constant 1 to 5 scale, we mathematically mapped our models' internal continuous scores to this exact range. This provides a measurable, real-world baseline of documented user satisfaction.

## Metrics Used & Why We Calculated Them
* **RMSE (Root Mean Squared Error):** Measures the average magnitude of prediction error. We calculated this to heavily penalize models whose continuous scores deviated too far from the true 1-5 star scale.
* **Pearson/Spearman Correlation:** Measures the linear and monotonic relationship trends. Calculated to ensure the AI's predicted sentiment trajectory moves in the exact same direction as actual customer ratings.
* **Accuracy & Macro-F1 Score:** Evaluates rigid classification tasks (Positive, Neutral, Negative). We specifically calculated **Macro-F1** to ensure fair evaluation across all sentiment blocks, preventing the system from becoming biased toward the overwhelmingly positive majority typical of e-commerce datasets.

## Pipeline Results (`comparison_summary_v2.csv`)
* **Conclusion:** Deep learning methods (BERT) generated the lowest continuous error and highest Macro-F1 score.
* **System Impact:** This rigorous mathematical validation definitively established BERT as the strongest and most reliable individual signal for our final forecasting engine.