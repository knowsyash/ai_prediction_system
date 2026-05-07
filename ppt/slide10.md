# Ensemble Analysis (Model Aggregation)

## Why Ensemble Modeling?
Relying on a single sentiment analyzer leaves room for bias. By aggregating multiple models, the system significantly improves prediction reliability and reduces variance.

## Implemented Techniques (`ensemble_analysis.py`)
* **Hard Voting:** Uses simple majority rule. If 2 out of 3 models predict "Positive," the final label is "Positive."
* **Soft Voting:** Averages the continuous predicted probabilities (or normalized scores) from each model. This accounts for model *confidence* rather than just the final label, providing a more reliable cumulative rating.
* **Bagging (Bootstrap Aggregating):** Generates multiple subset samples of the dataset, evaluating them to ensure high stability against outliers.

## Results (`ensemble_summary_v2.csv`)
* Ensemble methods (particularly Soft Voting and Bagging) consistently outperformed standalone models (like BERT or VADER) across all evaluation metrics.
* The output generates a highly stable underlying **Cumulative Rating** that serves as the primary numeric signal for our next-month forecasting engine.