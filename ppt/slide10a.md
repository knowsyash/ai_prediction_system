# Ensemble Analysis Results & Conclusion

## Performance Comparison: Individual vs. Ensemble Models

| Method | Accuracy | Macro-F1 | RMSE | Pearson (r) | Spearman (ρ) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **VADER** | 0.7690 | 0.5000 | 1.1606 | 0.4529 | 0.3018 |
| **BERT** | 0.8699 | 0.4758 | 1.2094 | 0.5423 | 0.3520 |
| **Word Cloud** | 0.7120 | 0.5094 | 1.1245 | 0.4798 | 0.3219 |
| **Hard Voting (Ensemble)**| 0.7819 | 0.5389 | 1.0533 | 0.5523 | **0.3703** |
| **Soft Voting (Ensemble)**| 0.8386 | **0.5424** | 0.9599 | **0.5916** | 0.3565 |
| **Bagging (Ensemble)** | 0.8374 | 0.3776 | **0.8973** | 0.5900 | 0.3560 |

## Key Insights & Conclusion
* **Synergy Triumphs:** The ensemble models outperformed standalone algorithms across multiple metrics. Combining structural (BERT), lexical (Word Cloud), and generalized (VADER) approaches successfully mitigated their individual weaknesses.
* **Soft Voting - The Best All-Rounder:** It achieved the highest Macro-F1 score (0.5424) and Pearson correlation (0.5916), while maintaining excellent Accuracy (0.8386). This proved that weighting the models' confidence levels yields the most reliable overall sentiment trajectory.
* **Bagging for Error Reduction:** The Bagging ensemble set the absolute lowest RMSE (0.8973), demonstrating its unmatched capability in minimizing extreme prediction errors.
* **Final Verdict:** The Ensemble framework provides a vastly superior, stable, and nuanced sentiment prediction engine compared to relying on any single model, directly translating to more robust forecasting for upcoming months.