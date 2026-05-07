# The Need for Ensemble Analysis

## Divergent Model Strengths (Overall Performance)

| Method | Accuracy | Macro-F1 | RMSE | Pearson (r) | Spearman (ρ) | Strategy / Strength |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BERT** | **0.8699** | 0.4758 | 1.2094 | **0.5423** | **0.3520** | Best Accuracy and directional trend |
| **Word Cloud**| 0.7120 | **0.5094** | **1.1245** | 0.4798 | 0.3219 | Lowest error (RMSE) & highest F1 |
| **VADER** | 0.7690 | 0.5000 | 1.1606 | 0.4529 | 0.3018 | Balanced performance across metrics |

* **Varied Performance:** The table above clearly shows that no single model uniformly dominated across all evaluation metrics.
* **Metric Specificity:** **BERT** excels in Accuracy and Correlation, whereas **Word Cloud** achieved the lowest RMSE and highest Macro-F1 score.
* **The Limitation:** Relying solely on BERT would increase overall error, while relying only on Word Cloud would reduce accuracy.


## Harnessing Collective Power
* **The Ensemble Strategy:** To maximize accuracy, stability, and robustness, we introduced an **Ensemble Analysis** approach.
* **Why it Works:** By systematically combining the distinct scoring mechanisms from our various models (**BERT, VADER, and Word Cloud lexical scoring**), the ensemble method smooths out individual algorithm biases.
* **System Impact:** This ensures we capture the "power of all," blending their unique strengths into a final predictive engine that is highly reliable and superior to any isolated model.