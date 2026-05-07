Here’s clean, **slide-ready content (7 slides)** based directly on your pipeline and math walkthrough . I’ve kept it **presentation-style + mathematical + example-driven**, so you can paste directly into PPT.

---

# **Slide 1: VADER Sentiment Analysis (Lexicon-Based)**

### **Concept**

* Rule-based sentiment model using predefined word scores
* Considers:

  * Word polarity
  * Intensifiers (e.g., *absolutely*)
  * Punctuation (!)
  * Conjunctions (*but*)

### **Mathematical Model**

\text{Compound Score} = \frac{S}{\sqrt{S^2 + \alpha}}

* Final Rating Mapping:
  [
  \text{Rating} = (compound \times 2) + 3
  ]

### **Example**

Review: *"I absolutely love the camera, it's amazing!"*

* Raw Score = 6.825
* Compound = 0.87
* Final Rating:
  [
  (0.87 \times 2) + 3 = 4.74
  ]

### **Key Insight**

* Fast, interpretable
* Works well for rule-based sentiment

---

# **Slide 2: Word Cloud Model (Custom Lexicon)**

### **Concept**

* Simple keyword-based scoring
* Domain-specific sentiment tracking

### **Mathematical Model**

[
\text{Keyword Ratio} = \frac{P - N}{P + N}
]
[
\text{Score} = ( \text{Keyword Ratio} \times 2) + 3
]

Where:

* (P) = positive keywords
* (N) = negative keywords

### **Example**

Review: *"love the camera, amazing"*

* Positive words (P) = 2
* Negative words (N) = 0

[
\text{Keyword Ratio} = \frac{2 - 0}{2 + 0} = 1.0
]
[
\text{Score} = (1.0 \times 2) + 3 = 5.0
]

### **Key Insight**

* Very simple and explainable
* Acts as baseline model

---

# **Slide 3: BERT Sentiment Model (Deep Learning)**

### **Concept**

* Transformer-based contextual NLP model
* Outputs probabilities instead of direct score

### **Mathematical Model**

[
\text{Rating} = 1.0 + (P_{pos} \times 4.0)
]
*Where $P_{pos}$ is the probability of the sentiment being Positive.*

### **Example**

Probabilities:

* Positive ($P_{pos}$) = 0.98

[
\text{Rating} = 1.0 + (0.98 \times 4.0) = 4.92
]

### **Key Insight**

* Captures context better than VADER
* Most accurate individual model

---

# **Slide 4: Ensemble – Hard Voting**

### **Concept**

* Majority voting among models
* Converts scores → classes

### **Rules**

* Identifies discrete predicted label (`Positive`, `Neutral`, or `Negative`) for each model.
* Takes the majority vote across the 3 models (Ties broken by VADER).
* Maps winning label to rating: Positive → 4.5, Neutral → 3.0, Negative → 1.5

### **Example**

| Model      | Local Label |
| ---------- | ----------- |
| VADER      | Positive    |
| BERT       | Neutral     |
| Word Cloud | Positive    |

➡ Majority Vote = **Positive** (Mapped to Rating = **4.5**)

### **Limitation**

* Loses numerical information
* Treats 3.9 and 3.1 equally

---

# **Slide 5: Ensemble – Soft Voting (Chosen Model)**

### **Concept**

* Weighted average of predictive scores based on model reliability
* Preserves full continuous sentiment information

### **Mathematical Model**

[
\text{Soft Vote} = (0.40 \times \text{VADER}) + (0.40 \times \text{BERT}) + (0.20 \times \text{Word Cloud})
]

### **Example**

[
(0.40 \times 4.74) + (0.40 \times 4.92) + (0.20 \times 5.0) = 1.896 + 1.968 + 1.0 = 4.864
]

### **Key Insight**

* More accurate than hard voting
* Used as final sentiment signal

---

# **Slide 6: Ensemble – Bagging (Bootstrap Aggregation)**

### **Concept**

* Reduce variance using multiple datasets
* Sampling with replacement

### **Mathematical Model**

[
\text{Final Prediction} = \frac{1}{N} \sum_{i=1}^{N} y_i
]

### **Example**

Predictions from samples:

* 4.43, 4.41, 4.45 …

[
\text{Final} \approx 4.435
]

### **Key Insight**

* Improves stability
* Reduces noise in predictions

---

# **Slide 7: Final Forecast (Linear + EMA + Ensemble)**

### **1. Linear Trend**

[
y = mx + b
]
Example:
[
(0.015 \times 14) + 4.32 = 4.53
]

---

### **2. Exponential Moving Average (EMA)**

S_t = \alpha y_t + (1-\alpha) S_{t-1}

Example:

* Final EMA = 4.615

---

### **3. Ensemble Sentiment Signal**

* Average soft vote = **4.160**

---

### **Final Weighted Prediction**

[
0.4(4.53) + 0.35(4.615) + 0.25(4.160) = 4.467
]

### **Key Insight**

* Combines:

  * Long-term trend
  * Recent momentum
  * Current sentiment

---

