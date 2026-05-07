# Sentiment Models (Score Calculations)

To effectively analyze sentiments, each model uses a distinct mathematical approach to calculate its final score before aggregation.

## 1. VADER (Compound Polarity Map)
VADER sums the valence scores of each word in the lexicon, applies rule-based intensity modifiers (e.g., "very"), and normalizes the score:
* **Compound Score:** Scaled exactly between -1 (Extreme Negative) and +1 (Extreme Positive).
* **Adaptation:** We linearly rescaled this score to match our 1 to 5 star rating scale mathematically.

## 2. BERT (Softmax Probability Calculation)
BERT generates raw logits ($z$) for each class. We apply the Softmax function to convert these into accurate confidence probabilities:
$$ P(class) = \frac{e^{z}}{\sum e^{z}} $$
* **Example:** Logits `[2.0, 1.0, 0.5]` convert to a **62% Negative probability ($P=0.62$)**.

## 3. Word Cloud Proxy (TF-IDF Weighting)
Our custom domain-specific baseline. It calculates Term Frequency-Inverse Document Frequency (TF-IDF) weights:
* Identifies words common in one sentiment class but rare in others.
* Positive words increment the base score; negative words deduct from it.