# Sentiment Analysis Scoring System

* **Detected Review:** "Camera is amazing and fast, but battery lags."

## Sentiment Formula (TF-IDF Proxy Concept)
* Final Score = Base Score + (Positive Keyword Frequency &times; Positive Weight) - (Negative Keyword Frequency &times; Negative Weight)

## Input Values
* **Base Score = 3.0** (Neutral starting point)
* **Positive Terms = 2** ("amazing", "fast") &rarr; predefined weight: +0.6 each
* **Negative Terms = 1** ("lags") &rarr; predefined weight: -0.8 each

## Calculation
* Final Score = 3.0 + (2 &times; 0.6) - (1 &times; 0.8)
* Final Score = 3.0 + 1.2 - 0.8
* **Final Score = 3.4**

## Final Result
* **Sentiment Level: NEUTRAL-POSITIVE (3.4 Stars)**
* **Action:** The model mathematically balances the mixed feedback, preventing the single negative keyword from completely destroying the rating.