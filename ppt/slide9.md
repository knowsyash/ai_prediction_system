# Sentiment Analysis Comparison & Methodology

## Models Evaluated
Our pipeline evaluates three distinct sentiment analysis techniques (`compare_methods_v2.py`):
1. **VADER:** A fast, lexicon-based baseline. It assigns predefined scores to words (e.g., `poor` &rarr; -2.1). However, it struggles with domain-specific terms (e.g., `heating` has no native score).
2. **BERT (Deep Learning):** A state-of-the-art transformer model. It reads text bidirectionally to capture complex context, sarcasm, and technical trade-offs (e.g., *"Great camera but terrible battery"*).
3. **Word Cloud Proxy:** A custom TF-IDF keyword scoring method used to provide high interpretability of recurring complaints.

## Evaluation & Validation
* **Ground Truth:** Model predictions were validated against the actual customer Star Ratings (1-5).
* **Metrics Used:** Performance was rigorously compared using **RMSE**, **Accuracy**, **Macro-F1**, and **Pearson/Spearman Correlation**.
* **Results (`comparison_summary_v2.csv`):** BERT significantly outperformed lexicon-based methods in correctly classifying nuanced smartphone feedback, establishing it as the strongest individual signal for our prediction engine.