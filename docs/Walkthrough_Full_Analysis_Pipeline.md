# Walkthrough: The Full Analysis Pipeline (A Mathematical Example)

**Version 1.0 - Last Updated: 2026-04-28**

## Introduction

This document provides a detailed, step-by-step walkthrough of the entire AI prediction pipeline, from individual review analysis to the final next-month forecast. We will trace the journey of three hypothetical sample reviews through each major stage:

1.  **Stage 1: Individual Sentiment Analysis** (VADER, BERT, Word Cloud)
2.  **Stage 2: Ensemble Analysis** (Hard Voting, Soft Voting)
3.  **Stage 3: Final Next-Month Prediction** (Time-Series and Sentiment Signal Combination)

This will serve as a practical, "on-paper" demonstration of the mathematical and logical operations performed by the scripts.

---

## Our Three Sample Reviews

Let's imagine our dataset contains the following three reviews for the "iPhone 16" for the month of "Jan 2026".

| Review ID | Actual Rating | Review Text                               |
|-----------|---------------|-------------------------------------------|
| 1         | 5             | "I absolutely love the new camera, it's amazing!" |
| 2         | 1             | "The battery life is bad, truly terrible."    |
| 3         | 4             | "Good screen, but the battery is just okay."  |

---

## Stage 1: Individual Sentiment Analysis

Each review is independently analyzed by our three sentiment models.

### Model 1: VADER (Lexicon-Based)

VADER works by looking up each word in a pre-built dictionary (a lexicon) where words are assigned sentiment scores.

#### **Review 1: "I absolutely love the new camera, it's amazing!"**
- **love:** +3.1
- **amazing:** +2.7
- **absolutely (intensifier):** Multiplies the score of the next word.
- **Calculation:** VADER sums the scores. The word "love" is intensified. Let's say the final normalized `compound` score is **+0.92**.
- **VADER Predicted Rating:** `(0.92 * 2) + 3 = 4.84`

#### **Review 2: "The battery life is bad, truly terrible."**
- **bad:** -2.5
- **terrible:** -3.0
- **truly (intensifier):** Intensifies "terrible".
- **Calculation:** The scores are summed. The final normalized `compound` score is **-0.85**.
- **VADER Predicted Rating:** `(-0.85 * 2) + 3 = 1.30`

#### **Review 3: "Good screen, but the battery is just okay."**
- **Good:** +1.9
- **but (conjunction):** Reduces the impact of the preceding clause.
- **okay:** +0.2
- **Calculation:** VADER recognizes the contrast. The positive score of "Good" is dampened by the "but". The final normalized `compound` score is **+0.25**.
- **VADER Predicted Rating:** `(0.25 * 2) + 3 = 3.50`

### Model 2: BERT (Neural Network)

BERT does not use a word list. It is a large neural network that understands context. We can't do the math by hand, but we can simulate its output probabilities.

#### **Review 1: "I absolutely love the new camera, it's amazing!"**
- **BERT's Thought Process:** Understands "love" and "amazing" in the context of a "camera" are strongly positive.
- **Output Probabilities:** { Positive: 0.98, Neutral: 0.01, Negative: 0.01 }
- **BERT Predicted Rating:** `(0.98 * 4) + (0.01 * 2.5) + (0.01 * 1) = 3.955` (using a weighted scale)

#### **Review 2: "The battery life is bad, truly terrible."**
- **BERT's Thought Process:** Understands "bad" and "terrible" in the context of "battery life" are strongly negative.
- **Output Probabilities:** { Positive: 0.02, Neutral: 0.03, Negative: 0.95 }
- **BERT Predicted Rating:** `(0.02 * 4) + (0.03 * 2.5) + (0.95 * 1) = 1.105`

#### **Review 3: "Good screen, but the battery is just okay."**
- **BERT's Thought Process:** Recognizes the mixed sentiment. "Good screen" is positive, but "battery is just okay" is neutral-to-negative, and the word "but" signals a contrast.
- **Output Probabilities:** { Positive: 0.40, Neutral: 0.55, Negative: 0.05 }
- **BERT Predicted Rating:** `(0.40 * 4) + (0.55 * 2.5) + (0.05 * 1) = 3.025`

### Model 3: Word Cloud (Custom Lexicon)

This model uses a simplified, custom lexicon. Let's assume its logic is similar to VADER but with different scores.

- **Review 1 Predicted Rating:** **4.50**
- **Review 2 Predicted Rating:** **1.50**
- **Review 3 Predicted Rating:** **3.00**

---

## Stage 2: Ensemble Analysis

Now we combine the predictions from Stage 1.

### Intermediate Results Table

| Review ID | VADER Pred. | BERT Pred. | Word Cloud Pred. |
|-----------|-------------|------------|------------------|
| 1         | 4.84        | 3.955      | 4.50             |
| 2         | 1.30        | 1.105      | 1.50             |
| 3         | 3.50        | 3.025      | 3.00             |

### Method 1: Hard Voting (Majority Rule)

We first convert each predicted rating into a class label (e.g., >= 4 is Positive, < 3 is Negative, else Neutral).

| Review ID | VADER Class | BERT Class | Word Cloud Class | **Hard Vote Result** |
|-----------|-------------|------------|------------------|----------------------|
| 1         | Positive    | Positive   | Positive         | **Positive**         |
| 2         | Negative    | Negative   | Negative         | **Negative**         |
| 3         | Neutral     | Neutral    | Neutral          | **Neutral**          |

### Method 2: Soft Voting (Averaging Scores)

This is the model chosen for the final sentiment signal. It works by simply averaging the predicted ratings from the individual models.

#### **Review 1:**
- **Calculation:** `(4.84 + 3.955 + 4.50) / 3`
- **Soft Vote Predicted Rating:** **4.432**

#### **Review 2:**
- **Calculation:** `(1.30 + 1.105 + 1.50) / 3`
- **Soft Vote Predicted Rating:** **1.302**

#### **Review 3:**
- **Calculation:** `(3.50 + 3.025 + 3.00) / 3`
- **Soft Vote Predicted Rating:** **3.175**

These Soft Vote scores are the final, refined sentiment predictions for each review.

---

## Stage 3: Final Next-Month Prediction

This stage uses the entire history of reviews, not just our three samples. Let's assume the following historical context for the "iPhone 16":
- **Previous 13 Months Average Ratings:** `[4.2, 4.3, 4.2, 4.4, 4.5, 4.4, 4.3, 4.5, 4.6, 4.5, 4.4, 4.5, 4.4]`
- **Current Month (Jan 2026) Average Actual Rating:** 4.455

### Signal 1: Linear Trend Projection

1.  **Create Time Series:** We have 14 data points (13 past months + the current month).
    - `x` (time index) = `[0, 1, 2, ..., 13]`
    - `y` (ratings) = `[4.2, 4.3, ..., 4.4, 4.455]`
2.  **Fit Line:** The script runs `numpy.polyfit` on `x` and `y`. Let's say this finds the best-fit line is:
    $$ y = 0.015x + 4.32 $$
3.  **Extrapolate:** We predict for the next month, which has a time index of `14`.
    $$ \text{Prediction} = (0.015 \times 14) + 4.32 = 0.21 + 4.32 = 4.53 $$
- **Linear Trend Signal:** **4.530**

### Signal 2: Exponential Smoothing

1.  **Use Time Series:** We use the same 14 data points.
2.  **Apply Smoothing:** The script uses an `alpha` of 0.30 (since we have >= 8 data points).
    - $S_0 = 4.2$
    - $S_1 = (0.30 \times 4.3) + (0.70 \times 4.2) = 4.23$
    - ... (this calculation is repeated for all 14 points) ...
    - Let's assume the final smoothed value after the 14th data point is calculated to be **4.615**.
- **Exponential Smoothing Signal:** **4.615**

### Signal 3: Ensemble Sentiment Signal

1.  **Isolate Current Month:** We look at all reviews for "iPhone 16" in "Jan 2026". Our three sample reviews are part of this set.
2.  **Average Soft Vote Scores:** We take the `soft_vote_pred_rating` for all reviews in this month and average them. Let's assume the average of all these scores (including our 4.432, 1.302, and 3.175) comes out to **4.160**.
- **Sentiment Signal:** **4.160**

### The Final Weighted Forecast

The iPhone 16 has 14 months of history, so we use the "Sufficient Data" weights (40% Linear, 35% Exp. Smooth, 25% Sentiment).

- **Calculation:**
$$ \text{Final Prediction} = (0.40 \times 4.530) + (0.35 \times 4.615) + (0.25 \times 4.160) $$
$$ \text{Final Prediction} = 1.812 + 1.61525 + 1.04 $$
$$ \text{Final Prediction} = 4.46725 $$

- **Final Rounded Prediction:** **4.467**

This final value is the project's official forecast for the iPhone 16's average rating for Feb 2026. It is a carefully balanced synthesis of long-term trends, recent momentum, and real-time market sentiment.
