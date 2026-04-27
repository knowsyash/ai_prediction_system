"""
ensemble_analysis.py  (v2 — uses cleaned final dataset)
========================================================
Ensemble techniques for sentiment-based cumulative rating prediction.

Data source:
  Reads comparison_results_v2.csv produced by
  3_sentimental_analysis/YS/compare_methods_v2.py
  (which uses the name-cleaned 2_dataset_final_folder CSVs)

Methods implemented:
  1. Individual baselines    - VADER, BERT, Word Cloud (already computed)
  2. Hard Voting             - majority class wins among 3 models
  3. Soft Voting             - average of predicted rating scores
  4. Bagging (bootstrap)     - 50 bootstrap samples, aggregate by mean

Evaluation metrics:
  - Accuracy, Macro-F1
  - RMSE (vs 1-5 rating scale)
  - Pearson r, Spearman rho (correlation with human rating)
  - Consistency (std dev of bootstrap predictions)
  - Robustness (per-class F1 on minority classes)

Outputs (v2 suffix):
  ensemble_results_v2.csv       - per-review ensemble labels and predicted ratings
  ensemble_summary_v2.csv       - all method metrics side by side
  ensemble_metric_bar_v2.png    - bar chart comparison
  ensemble_confusion_*_v2.png   - confusion matrices for ensemble methods
  ensemble_reliability_v2.png   - bootstrap prediction stability plot
  cumulative_ratings_v2.csv/png - device-level aggregated predictions
"""

import os
import math
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import pearsonr, spearmanr, mode
from sklearn.metrics import (
    confusion_matrix, accuracy_score, f1_score,
    classification_report, mean_squared_error
)

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
# Read v2 results from YS folder (cleaned final dataset)
YS_DIR      = os.path.normpath(os.path.join(BASE_DIR, "../3_sentimental_analysis/YS"))
RESULTS_CSV = os.path.join(YS_DIR, "comparison_results_v2.csv")
OUT_DIR     = BASE_DIR

LABEL_ORDER = ["Positive", "Neutral", "Negative"]

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def rating_to_label(r):
    if r >= 4: return "Positive"
    if r == 3: return "Neutral"
    return "Negative"

def score_to_label(score, threshold_pos=0.05, threshold_neg=-0.05):
    """Generic: maps a signed score (-1..+1) to 3-class label."""
    if score >= threshold_pos: return "Positive"
    if score <= threshold_neg: return "Negative"
    return "Neutral"

def compute_metrics(y_true_lbl, y_pred_lbl, y_true_rat, y_pred_rat, method):
    """Return a dict of all evaluation metrics."""
    valid_mask = (
        pd.notna(y_pred_lbl) & pd.notna(y_pred_rat) &
        (y_pred_lbl != "Unknown")
    )
    tl = y_true_lbl[valid_mask]
    pl = y_pred_lbl[valid_mask]
    tr = y_true_rat[valid_mask]
    pr = y_pred_rat[valid_mask]

    if len(tl) == 0:
        return {}

    acc  = accuracy_score(tl, pl)
    f1   = f1_score(tl, pl, average="macro", labels=LABEL_ORDER, zero_division=0)
    rmse = math.sqrt(mean_squared_error(tr, pr))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pearson_r, _  = pearsonr(tr, pr)
        spearman_r, _ = spearmanr(tr, pr)

    return {
        "Method":       method,
        "N":            int(len(tl)),
        "Accuracy":     round(acc,  4),
        "Macro_F1":     round(f1,   4),
        "RMSE":         round(rmse, 4),
        "Pearson_r":    round(pearson_r,  4),
        "Spearman_rho": round(spearman_r, 4),
    }


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 – LOAD INDIVIDUAL RESULTS
# ──────────────────────────────────────────────────────────────────────────────
def load_results():
    if not os.path.exists(RESULTS_CSV):
        raise FileNotFoundError(
            f"Run 3_sentimental_analysis/YS/compare_methods_v2.py first.\n"
            f"Expected file: {RESULTS_CSV}"
        )
    df = pd.read_csv(RESULTS_CSV)
    df["true_label"] = df["rating"].apply(rating_to_label)
    # Handle BERT "Unknown" (when transformers not installed)
    if "bert_label" not in df.columns:
        df["bert_label"]       = "Unknown"
        df["bert_score"]       = np.nan
        df["bert_pred_rating"] = np.nan
    print(f"  Loaded {len(df)} reviews from comparison_results_v2.csv (cleaned dataset)")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 – CUMULATIVE RATING per item (device-level aggregation)
# ──────────────────────────────────────────────────────────────────────────────
def compute_cumulative_ratings(df):
    """
    Aggregate individual review ratings to cumulative device-level scores.
    This shows what each method 'says' the overall product sentiment is.
    """
    rows = []
    for device in df["device"].unique():
        sub = df[df["device"] == device]
        row = {"Device": device, "N_reviews": len(sub)}

        # Ground truth: mean actual rating
        row["Actual_mean_rating"]  = round(sub["rating"].mean(), 3)
        row["Actual_mode_rating"]  = int(sub["rating"].mode()[0])
        row["Actual_pct_positive"] = round((sub["true_label"] == "Positive").mean() * 100, 1)

        # VADER cumulative
        if "vader_pred_rating" in sub.columns:
            row["VADER_mean_rating"]  = round(sub["vader_pred_rating"].mean(), 3)
            row["VADER_pct_positive"] = round((sub["vader_label"] == "Positive").mean() * 100, 1)

        # BERT cumulative
        if "bert_pred_rating" in sub.columns and sub["bert_pred_rating"].notna().any():
            row["BERT_mean_rating"]  = round(sub["bert_pred_rating"].mean(), 3)
            row["BERT_pct_positive"] = round((sub["bert_label"] == "Positive").mean() * 100, 1)
        else:
            row["BERT_mean_rating"]  = None
            row["BERT_pct_positive"] = None

        # Word Cloud cumulative
        if "wc_pred_rating" in sub.columns:
            row["WC_mean_rating"]  = round(sub["wc_pred_rating"].mean(), 3)
            row["WC_pct_positive"] = round((sub["wc_label"] == "Positive").mean() * 100, 1)

        rows.append(row)

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3a – HARD VOTING (majority class among 3 models)
# ──────────────────────────────────────────────────────────────────────────────
def hard_voting(df):
    """
    For each review: take the majority label among VADER, BERT, Word Cloud.
    Ties broken by VADER (most reliable single model).
    """
    bert_available = "bert_label" in df.columns and (df["bert_label"] != "Unknown").any()

    votes = df[["vader_label", "wc_label"]].copy()
    if bert_available:
        votes["bert_label"] = df["bert_label"]

    def majority(row):
        labels = [v for v in row.values if v not in (None, "Unknown", float("nan"))]
        if not labels:
            return "Positive"  # default
        counts = {}
        for l in labels:
            counts[l] = counts.get(l, 0) + 1
        max_count = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_count]
        # Tie-break: prefer VADER's label
        if len(winners) == 1:
            return winners[0]
        return row.get("vader_label", winners[0])

    df["hard_vote_label"] = votes.apply(majority, axis=1)

    # Map label to predicted rating midpoint
    label_to_rating = {"Positive": 4.5, "Neutral": 3.0, "Negative": 1.5}
    df["hard_vote_pred_rating"] = df["hard_vote_label"].map(label_to_rating)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3b – SOFT VOTING (weighted average of continuous scores)
# ──────────────────────────────────────────────────────────────────────────────
def soft_voting(df):
    """
    Average the predicted rating scores from all available models.
    If BERT is available: weight VADER=0.4, BERT=0.4, WC=0.2
    If BERT unavailable:  weight VADER=0.6, WC=0.4
    """
    bert_available = "bert_pred_rating" in df.columns and df["bert_pred_rating"].notna().any()

    if bert_available:
        df["soft_vote_pred_rating"] = (
            0.40 * df["vader_pred_rating"] +
            0.40 * df["bert_pred_rating"]  +
            0.20 * df["wc_pred_rating"]
        ).clip(1, 5)
    else:
        df["soft_vote_pred_rating"] = (
            0.60 * df["vader_pred_rating"] +
            0.40 * df["wc_pred_rating"]
        ).clip(1, 5)

    # Convert continuous score back to 3-class label
    def pred_to_label(r):
        if r >= 3.75: return "Positive"
        if r <= 2.25: return "Negative"
        return "Neutral"

    df["soft_vote_label"] = df["soft_vote_pred_rating"].apply(pred_to_label)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3c – BAGGING (Bootstrap Aggregating)
# ──────────────────────────────────────────────────────────────────────────────
def bagging(df, n_bootstraps=50, sample_frac=0.80, random_seed=42):
    """
    Simulate bagging by:
      1. Drawing B bootstrap samples (with replacement) of size ~80% of data
      2. Computing average VADER + WC score on each sample to get per-review weights
      3. Aggregating across samples via soft average
      Note: Since VADER/WC are deterministic, bagging tests prediction STABILITY.
             BERT is included in final aggregation when available.
    """
    rng = np.random.default_rng(random_seed)
    n   = len(df)
    size = max(1, int(n * sample_frac))

    # Run B bootstrap iterations; store the predicted rating for each review
    all_preds = np.zeros((n_bootstraps, n))

    bert_available = "bert_pred_rating" in df.columns and df["bert_pred_rating"].notna().any()
    vader  = df["vader_pred_rating"].values
    wc     = df["wc_pred_rating"].values
    if bert_available:
        bert = df["bert_pred_rating"].values
    else:
        bert = None

    for b in range(n_bootstraps):
        # Sample indices with replacement
        idx = rng.choice(n, size=size, replace=True)

        # Compute local per-sample average for VADER and WC
        # (BERT is fixed — only VADER/WC are re-scored in the bootstrap)
        local_vader = vader[idx]
        local_wc    = wc[idx]

        # Mean score from this bootstrap (2-model or 3-model)
        if bert is not None:
            local_bert = bert[idx]
            local_avg  = (0.40 * local_vader + 0.40 * local_bert + 0.20 * local_wc)
        else:
            local_avg  = (0.60 * local_vader + 0.40 * local_wc)

        # Assign bootstrap predictions back to ALL indices
        # (each review may appear 0 to ~5 times in the bootstrap; compute mean of OOB)
        bootstrap_scores = np.full(n, np.nan)
        for pos, orig_idx in enumerate(idx):
            if np.isnan(bootstrap_scores[orig_idx]):
                bootstrap_scores[orig_idx] = local_avg[pos]
            else:
                bootstrap_scores[orig_idx] = (bootstrap_scores[orig_idx] + local_avg[pos]) / 2.0

        # Fill any NaN (OOB samples) with global mean
        global_mean = np.nanmean(local_avg)
        bootstrap_scores[np.isnan(bootstrap_scores)] = global_mean

        all_preds[b, :] = bootstrap_scores

    df["bagging_pred_rating"] = np.mean(all_preds, axis=0).clip(1, 5)
    df["bagging_pred_std"]    = np.std(all_preds,  axis=0)   # consistency measure

    def pred_to_label(r):
        if r >= 3.75: return "Positive"
        if r <= 2.25: return "Negative"
        return "Neutral"

    df["bagging_label"] = df["bagging_pred_rating"].apply(pred_to_label)
    return df, all_preds


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 – PLOTS
# ──────────────────────────────────────────────────────────────────────────────
def plot_confusion(df, label_col, method_name):
    valid = df[[label_col, "true_label"]].dropna()
    valid = valid[valid[label_col] != "Unknown"]
    if valid.empty:
        return
    cm = confusion_matrix(valid["true_label"], valid[label_col], labels=LABEL_ORDER)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=LABEL_ORDER, yticklabels=LABEL_ORDER, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix - {method_name}")
    plt.tight_layout()
    fname = os.path.join(OUT_DIR, f"ensemble_confusion_{method_name.replace(' ', '_')}_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


def plot_metric_comparison(summary_df):
    metrics  = ["Accuracy", "Macro_F1", "Pearson_r"]
    methods  = summary_df["Method"].tolist()
    colors   = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD"]

    x     = np.arange(len(metrics))
    width = 0.12
    n     = len(methods)
    offsets = np.linspace(-width * n / 2, width * n / 2, n)

    fig, ax = plt.subplots(figsize=(11, 6))
    for i, (method, offset) in enumerate(zip(methods, offsets)):
        row  = summary_df[summary_df["Method"] == method].iloc[0]
        vals = [row.get(m, 0) for m in metrics]
        bars = ax.bar(x + offset, vals, width, label=method,
                      color=colors[i % len(colors)], alpha=0.88)
        for bar, val in zip(bars, vals):
            if val and val > 0.01:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.008,
                        f"{val:.3f}", ha="center", va="bottom",
                        fontsize=6.5, rotation=60)

    ax.set_xticks(x)
    ax.set_xticklabels(["Accuracy", "Macro-F1", "Pearson r"], fontsize=12)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Individual vs Ensemble Methods - Performance Comparison", fontsize=13)
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    ax.axhline(y=0.7841, color="#4C72B0", linestyle="--", alpha=0.3, linewidth=1)
    plt.tight_layout()
    fname = os.path.join(OUT_DIR, "ensemble_metric_bar_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


def plot_rmse_comparison(summary_df):
    methods = summary_df["Method"].tolist()
    rmses   = [summary_df[summary_df["Method"] == m]["RMSE"].iloc[0] for m in methods]
    colors  = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD"]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(methods, rmses, color=colors[:len(methods)], alpha=0.85)
    for bar, val in zip(bars, rmses):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("RMSE (lower is better)", fontsize=11)
    ax.set_title("RMSE: Individual vs Ensemble Methods", fontsize=12)
    ax.set_ylim(0, max(rmses) * 1.20)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    fname = os.path.join(OUT_DIR, "ensemble_rmse_bar_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


def plot_bootstrap_stability(df, all_preds):
    """Show how stable BAGGING predictions are per review (std across bootstraps)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: histogram of per-review prediction std
    ax = axes[0]
    std_vals = df["bagging_pred_std"].dropna()
    if len(std_vals) > 0:
        ax.hist(std_vals, bins=40, color="#8172B2", alpha=0.8, edgecolor="white")
        mean_std = std_vals.mean()
        ax.axvline(mean_std, color="red", linestyle="--",
                   label=f"Mean std = {mean_std:.3f}")
    ax.set_xlabel("Std Dev of Rating Predictions (across 50 bootstraps)")
    ax.set_ylabel("Number of Reviews")
    ax.set_title("Bagging Prediction Stability\n(lower std = more consistent)")
    ax.legend()

    # Right: scatter of actual rating vs bagging std (reviews with low rating have higher uncertainty?)
    ax = axes[1]
    for label, color in [("Positive", "#55A868"), ("Neutral", "#CCB974"), ("Negative", "#C44E52")]:
        sub = df[df["true_label"] == label]
        ax.scatter(sub["rating"], sub["bagging_pred_std"],
                   alpha=0.15, s=8, color=color, label=label)
    ax.set_xlabel("Actual Rating (1-5)")
    ax.set_ylabel("Bagging Prediction Std Dev")
    ax.set_title("Uncertainty by Rating Class")
    ax.legend()

    plt.suptitle("Bagging Robustness Analysis (50 Bootstrap Samples)", fontsize=12)
    plt.tight_layout()
    fname = os.path.join(OUT_DIR, "ensemble_reliability_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


def plot_cumulative_ratings(cum_df):
    devices = cum_df["Device"].tolist()
    x       = np.arange(len(devices))
    width   = 0.18

    fig, ax = plt.subplots(figsize=(10, 6))
    cols  = ["Actual_mean_rating", "VADER_mean_rating", "BERT_mean_rating", "WC_mean_rating"]
    names = ["Actual (Ground Truth)", "VADER", "BERT", "Word Cloud"]
    colors = ["#333333", "#4C72B0", "#55A868", "#C44E52"]

    for i, (col, name, color) in enumerate(zip(cols, names, colors)):
        if col in cum_df.columns:
            vals = [cum_df[cum_df["Device"] == d][col].values[0] or 0 for d in devices]
            ax.bar(x + i * width, vals, width, label=name, color=color, alpha=0.85)

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(devices, fontsize=11)
    ax.set_ylabel("Mean Predicted Rating (1-5)")
    ax.set_title("Cumulative Rating Prediction per Device")
    ax.set_ylim(0, 5.5)
    ax.legend()
    plt.tight_layout()
    fname = os.path.join(OUT_DIR, "cumulative_ratings_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print("\n=== Ensemble Sentiment Analysis ===\n")

    # 1. Load
    print("[1] Loading comparison results ...")
    df = load_results()
    print()

    # 2. Cumulative ratings
    print("[2] Computing cumulative ratings per device ...")
    cum_df = compute_cumulative_ratings(df)
    print(cum_df.to_string(index=False))
    cum_csv = os.path.join(OUT_DIR, "cumulative_ratings_v2.csv")
    cum_df.to_csv(cum_csv, index=False)
    print(f"\n  Cumulative ratings saved -> {os.path.basename(cum_csv)}\n")

    # 3. Ensemble methods
    print("[3a] Applying Hard Voting ...")
    df = hard_voting(df)

    print("[3b] Applying Soft Voting ...")
    df = soft_voting(df)

    print("[3c] Applying Bagging (50 bootstrap samples) ...")
    df, all_preds = bagging(df, n_bootstraps=50)
    print()

    # 4. Compute metrics for all 6 methods
    print("[4] Computing metrics for all methods ...\n")

    METHODS = [
        ("VADER",       "vader_label",      "vader_pred_rating"),
        ("BERT",        "bert_label",        "bert_pred_rating"),
        ("Word Cloud",  "wc_label",          "wc_pred_rating"),
        ("Hard Voting", "hard_vote_label",   "hard_vote_pred_rating"),
        ("Soft Voting", "soft_vote_label",   "soft_vote_pred_rating"),
        ("Bagging",     "bagging_label",     "bagging_pred_rating"),
    ]

    summary_rows = []
    for name, lbl_col, rat_col in METHODS:
        m = compute_metrics(
            df["true_label"], df[lbl_col],
            df["rating"],     df[rat_col],
            name
        )
        if m:
            summary_rows.append(m)

    summary_df = pd.DataFrame(summary_rows)
    print("=== METRIC SUMMARY ===")
    print(summary_df.to_string(index=False))

    # Also compute consistency for bagging
    mean_std = df["bagging_pred_std"].mean()
    print(f"\n  Bagging consistency (mean std across 50 bootstraps): {mean_std:.4f}")
    print(f"  (lower = more stable predictions)\n")

    # Per-class breakdown
    print("=== CLASSIFICATION REPORTS ===\n")
    for name, lbl_col, _ in METHODS:
        valid = df[[lbl_col, "true_label"]].dropna()
        valid = valid[valid[lbl_col] != "Unknown"]
        if valid.empty:
            continue
        print(f"--- {name} ---")
        print(classification_report(
            valid["true_label"], valid[lbl_col],
            labels=LABEL_ORDER, zero_division=0
        ))

    # Save full results
    ens_csv = os.path.join(OUT_DIR, "ensemble_results_v2.csv")
    df.to_csv(ens_csv, index=False)
    print(f"  Full results saved -> {os.path.basename(ens_csv)}")

    sum_csv = os.path.join(OUT_DIR, "ensemble_summary_v2.csv")
    summary_df.to_csv(sum_csv, index=False)
    print(f"  Summary saved      -> {os.path.basename(sum_csv)}\n")

    # 5. Plots
    print("[5] Generating plots ...")
    for name, lbl_col, _ in METHODS:
        if name in ["VADER", "BERT", "Word Cloud"]:
            continue   # already have confusion matrices from compare_methods.py
        plot_confusion(df, lbl_col, name)

    plot_metric_comparison(summary_df)
    plot_rmse_comparison(summary_df)
    plot_bootstrap_stability(df, all_preds)
    plot_cumulative_ratings(cum_df)

    print("\n=== Done ===\n")


if __name__ == "__main__":
    main()
