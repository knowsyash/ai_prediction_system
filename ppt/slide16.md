# Ensemble Analysis Scoring System

* **Detected Target:** Aggregating model predictions for robust accuracy.

## Ensemble Formula (Soft Voting)
* Ensemble Rating = (BERT Prediction &times; 0.5) + (VADER Prediction &times; 0.3) + (Word Cloud Proxy &times; 0.2)

## Input Values (Example: Sample Review)
* **BERT Score = 4.2 stars** (Deep learning detects complex positive nuance)
* **VADER Score = 3.8 stars** (Lexicon detects generally positive words)
* **Word Cloud Proxy = 4.0 stars** (TF-IDF finds moderate positive frequency)

## Calculation
* Ensemble Rating = (4.2 &times; 0.5) + (3.8 &times; 0.3) + (4.0 &times; 0.2)
* Ensemble Rating = 2.1 + 1.14 + 0.80
* **Ensemble Rating = 4.04**

## Final Result
* **Cumulative Rating: 4.04 Stars**
* **Action:** The system successfully mitigates VADER's slight under-prediction by giving more trust (weight) to BERT, resulting in a highly stable final score.