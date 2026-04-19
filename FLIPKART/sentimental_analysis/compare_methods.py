"""
compare_methods.py
==================
Quantitative comparison of three sentiment analysis approaches:
  1. VADER (vaderSentiment)          — lexicon-based, no training
  2. BERT  (transformers pipeline)   — deep-learning, pre-trained
  3. Word Cloud category proxy       — TF-IDF keyword scoring

Ground truth: Flipkart star ratings (1–5) for iPhone 15, iPhone 16, iQOO Z10.

Metrics produced
----------------
  • Pearson r and Spearman ρ (correlation with rating)
  • RMSE (root mean squared error vs rating on a 1–5 scale)
  • Accuracy / Macro-F1 (3-class: Positive / Neutral / Negative)
  • Confusion matrix per method

Usage
-----
    python compare_methods.py

Outputs
-------
  comparison_results.csv   — per-review scores + ground truth
  comparison_summary.csv   — aggregated metrics table
  confusion_*.png          — confusion matrix heatmaps
  method_correlation.png   — scatter plots of predicted vs actual
"""

import os
import re
import math
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # headless – no Tk required
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    f1_score,
    classification_report,
    mean_squared_error,
)

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
DATASETS = {
    "iPhone 16": r"../augmented_data/iphone16_augmented.csv",
    "iPhone 15": r"../augmented_data/iphone15_augmented.csv",
    "iQOO Z10":  r"../augmented_data/iqoo_z10_augmented.csv",
}

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_CSV  = os.path.join(OUTPUT_DIR, "comparison_results.csv")
SUMMARY_CSV  = os.path.join(OUTPUT_DIR, "comparison_summary.csv")

# Rating → sentiment label mapping (ground truth)
def rating_to_label(r):
    if r >= 4:  return "Positive"
    if r == 3:  return "Neutral"
    return "Negative"

# Sentiment label → numeric mid-point for RMSE
LABEL_TO_RATING = {"Positive": 4.5, "Neutral": 3.0, "Negative": 1.5}

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 – LOAD & CLEAN DATA
# ──────────────────────────────────────────────────────────────────────────────
def load_data():
    frames = []
    base = os.path.dirname(os.path.abspath(__file__))
    for device, rel_path in DATASETS.items():
        full_path = os.path.normpath(os.path.join(base, rel_path))
        if not os.path.exists(full_path):
            print(f"  [SKIP] {device}: file not found -> {full_path}")
            continue
        df = pd.read_csv(full_path)
        df = df[["rating", "review_text"]].dropna()
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df = df.dropna(subset=["rating"])
        df["rating"] = df["rating"].astype(int).clip(1, 5)
        df = df[df["review_text"].str.strip() != ""]
        df["device"] = device
        df["true_label"] = df["rating"].apply(rating_to_label)
        frames.append(df)
        print(f"  Loaded {device}: {len(df)} reviews")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2a – VADER
# ──────────────────────────────────────────────────────────────────────────────
def run_vader(df):
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        print("  [WARN] vaderSentiment not installed (pip install vaderSentiment)")
        df["vader_compound"] = np.nan
        df["vader_label"]    = "Unknown"
        return df

    sia = SentimentIntensityAnalyzer()
    def score(text):
        try:
            return sia.polarity_scores(str(text))["compound"]
        except Exception:
            return 0.0

    df["vader_compound"] = df["review_text"].apply(score)
    df["vader_label"] = df["vader_compound"].apply(
        lambda c: "Positive" if c >= 0.05 else ("Negative" if c <= -0.05 else "Neutral")
    )
    # Map compound (−1…+1) to rating scale (1…5)
    df["vader_pred_rating"] = 3.0 + 2.0 * df["vader_compound"]  # linear projection
    df["vader_pred_rating"]  = df["vader_pred_rating"].clip(1, 5)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2b – BERT (distilbert-base-uncased-finetuned-sst-2-english)
# ──────────────────────────────────────────────────────────────────────────────
def run_bert(df):
    try:
        from transformers import pipeline
        print("  Loading BERT pipeline ...")
        clf = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
    except ImportError:
        print("  [WARN] transformers not installed (pip install transformers torch)")
        df["bert_label"]       = "Unknown"
        df["bert_score"]       = np.nan
        df["bert_pred_rating"] = np.nan
        return df

    BATCH = 64
    labels, scores = [], []
    texts = df["review_text"].fillna("").astype(str).tolist()

    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        try:
            results = clf(batch)
        except Exception as e:
            print(f"  [WARN] BERT batch {i}–{i+BATCH} failed: {e}")
            results = [{"label": "POSITIVE", "score": 0.5}] * len(batch)
        for r in results:
            lbl = r["label"].upper()
            sc  = r["score"]
            if lbl == "POSITIVE":
                labels.append("Positive")
                scores.append(sc)          # probability of positive
            else:
                labels.append("Negative")
                scores.append(1.0 - sc)    # invert → "positive probability"
        if (i // BATCH) % 10 == 0:
            print(f"    BERT progress: {min(i+BATCH, len(texts))}/{len(texts)}")

    # Convert to 3-class + numeric rating
    def bert_to_3class(pos_prob):
        if pos_prob >= 0.60:    return "Positive"
        if pos_prob <= 0.40:    return "Negative"
        return "Neutral"

    df["bert_label"]       = [bert_to_3class(s) for s in scores]
    df["bert_score"]       = scores
    # Map positive probability (0…1) to rating (1…5)
    df["bert_pred_rating"] = (1.0 + 4.0 * np.array(scores)).clip(1, 5)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2c – Word Cloud / keyword TF-IDF proxy
#   We build simple signed keyword scores using a manually crafted lexicon.
#   This mimics what "Word Cloud" frequency analysis tells us: the most
#   prominent words are positive / negative feature mentions.
# ──────────────────────────────────────────────────────────────────────────────
POSITIVE_WORDS = {
    "amazing", "excellent", "awesome", "fantastic", "perfect", "love", "great",
    "superb", "outstanding", "best", "wonderful", "brilliant", "super",
    "fabulous", "good", "nice", "smooth", "fast", "powerful", "premium",
    "recommend", "happy", "satisfied", "worth", "beautiful", "impressive",
    "terrific", "mind-blowing", "classy", "lovely", "compact",
    # domain-specific positives
    "crisp", "clear", "vivid", "responsive", "accurate", "reliable", "efficient",
}
NEGATIVE_WORDS = {
    "bad", "poor", "terrible", "worst", "horrible", "useless", "disappointed",
    "disappointing", "slow", "lag", "laggy", "overheating", "hot", "heating",
    "drain", "draining", "blinking", "hanging", "freeze", "crash", "defective",
    "waste", "overrated", "boring", "problem", "issue", "not working",
    # domain-specific negatives
    "scratched", "broken", "damaged", "fake", "refurbished", "overprice",
}

def wc_score(text):
    """Return a signed score in [−1, +1] based on keyword counting."""
    words = re.findall(r"[a-z]+", str(text).lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total   # ranges −1 to +1

def run_wordcloud_proxy(df):
    df["wc_score"] = df["review_text"].apply(wc_score)
    df["wc_label"] = df["wc_score"].apply(
        lambda s: "Positive" if s > 0.1 else ("Negative" if s < -0.1 else "Neutral")
    )
    # Map to rating scale
    df["wc_pred_rating"] = (3.0 + 2.0 * df["wc_score"]).clip(1, 5)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 – METRICS
# ──────────────────────────────────────────────────────────────────────────────
def compute_metrics(df, pred_label_col, pred_rating_col, method_name):
    valid = df[[pred_label_col, pred_rating_col, "true_label", "rating", "device"]].dropna()
    if valid.empty:
        return {}

    y_true_lbl  = valid["true_label"]
    y_pred_lbl  = valid[pred_label_col]
    y_true_rat  = valid["rating"]
    y_pred_rat  = valid[pred_rating_col]

    acc     = accuracy_score(y_true_lbl, y_pred_lbl)
    f1      = f1_score(y_true_lbl, y_pred_lbl, average="macro", zero_division=0)
    rmse    = math.sqrt(mean_squared_error(y_true_rat, y_pred_rat))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r_pearson, _ = pearsonr(y_true_rat, y_pred_rat)
        r_spearman, _ = spearmanr(y_true_rat, y_pred_rat)

    return {
        "Method":         method_name,
        "N":              len(valid),
        "Accuracy":       round(acc,  4),
        "Macro_F1":       round(f1,   4),
        "RMSE":           round(rmse, 4),
        "Pearson_r":      round(r_pearson,  4),
        "Spearman_rho":   round(r_spearman, 4),
    }


def per_device_metrics(df, pred_label_col, pred_rating_col, method_name):
    rows = []
    for dev in df["device"].unique():
        sub = df[df["device"] == dev]
        m = compute_metrics(sub, pred_label_col, pred_rating_col, method_name)
        if m:
            m["Device"] = dev
            rows.append(m)
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 – PLOTS
# ──────────────────────────────────────────────────────────────────────────────
METHODS = [
    ("VADER",      "vader_label",  "vader_pred_rating"),
    ("BERT",       "bert_label",   "bert_pred_rating"),
    ("Word Cloud", "wc_label",     "wc_pred_rating"),
]

def plot_confusion(df, label_col, method_name):
    labels = ["Positive", "Neutral", "Negative"]
    valid = df[[label_col, "true_label"]].dropna()
    if valid.empty:
        return
    cm = confusion_matrix(valid["true_label"], valid[label_col], labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual (Rating-based)")
    ax.set_title(f"Confusion Matrix — {method_name}")
    plt.tight_layout()
    fname = os.path.join(OUTPUT_DIR, f"confusion_{method_name.replace(' ', '_')}.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {fname}")


def plot_correlations(df):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (name, _, pred_rat) in zip(axes, METHODS):
        valid = df[["rating", pred_rat]].dropna()
        if valid.empty:
            ax.set_title(f"{name} — no data")
            continue
        ax.scatter(valid["rating"], valid[pred_rat], alpha=0.15, s=10,
                   color="#4C72B0")
        ax.plot([1, 5], [1, 5], "r--", linewidth=1.5, label="Perfect")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r, _ = pearsonr(valid["rating"], valid[pred_rat])
        ax.set_xlabel("Actual Rating (1–5)")
        ax.set_ylabel("Predicted Rating (1–5)")
        ax.set_title(f"{name}\nPearson r = {r:.3f}")
        ax.set_xlim(0.5, 5.5)
        ax.set_ylim(0.5, 5.5)
        ax.legend(fontsize=8)
    plt.suptitle("Predicted vs Actual Rating — All Devices", fontsize=13, y=1.02)
    plt.tight_layout()
    fname = os.path.join(OUTPUT_DIR, "method_correlation.png")
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {fname}")


def plot_metric_bar(summary_df):
    metrics = ["Accuracy", "Macro_F1", "Pearson_r"]
    methods = summary_df["Method"].tolist()
    x = np.arange(len(metrics))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, method in enumerate(methods):
        row = summary_df[summary_df["Method"] == method].iloc[0]
        vals = [row[m] for m in metrics]
        bars = ax.bar(x + i * width, vals, width, label=method)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Score")
    ax.set_title("Performance Comparison — VADER vs BERT vs Word Cloud")
    ax.legend()
    plt.tight_layout()
    fname = os.path.join(OUTPUT_DIR, "metric_comparison.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {fname}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print("\n=== Sentiment Method Comparison ===\n")

    # 1. Load
    print("[1] Loading datasets ...")
    df = load_data()
    if df.empty:
        print("  No data found. Check DATASETS paths.")
        return
    print(f"  Total reviews: {len(df)}\n")

    # 2. Run each method
    print("[2a] Running VADER ...")
    df = run_vader(df)

    print("[2b] Running BERT ...")
    df = run_bert(df)

    print("[2c] Running Word Cloud proxy ...")
    df = run_wordcloud_proxy(df)

    # 3. Save full results
    df.to_csv(RESULTS_CSV, index=False)
    print(f"\n  Full results saved -> {RESULTS_CSV}")

    # 4. Compute summary metrics (all devices combined)
    print("\n[3] Computing metrics ...\n")
    summary_rows = []
    detail_rows  = []

    for name, lbl_col, rat_col in METHODS:
        m_all = compute_metrics(df, lbl_col, rat_col, name)
        if m_all:
            m_all["Device"] = "ALL"
            summary_rows.append(m_all)

        per_dev = per_device_metrics(df, lbl_col, rat_col, name)
        detail_rows.extend(per_dev)

    summary_df = pd.DataFrame(summary_rows)
    detail_df  = pd.DataFrame(detail_rows)

    # Print summary
    print("=== OVERALL METRICS ===")
    print(summary_df.to_string(index=False))
    print("\n=== PER-DEVICE METRICS ===")
    print(detail_df.to_string(index=False))

    # Save
    combined = pd.concat([summary_df.assign(Scope="Overall"),
                          detail_df.rename(columns={"Device": "Device"}).assign(Scope="PerDevice")],
                         ignore_index=True)
    combined.to_csv(SUMMARY_CSV, index=False)
    print(f"\n  Summary CSV -> {SUMMARY_CSV}")

    # 5. Plots
    print("\n[4] Generating plots ...")
    for name, lbl_col, _ in METHODS:
        plot_confusion(df, lbl_col, name)
    plot_correlations(df)
    if not summary_df.empty:
        plot_metric_bar(summary_df)

    # 6. Print classification reports
    print("\n[5] Classification Reports\n")
    for name, lbl_col, _ in METHODS:
        valid = df[[lbl_col, "true_label"]].dropna()
        if valid.empty:
            continue
        print(f"--- {name} ---")
        print(classification_report(valid["true_label"], valid[lbl_col],
                                    labels=["Positive", "Neutral", "Negative"],
                                    zero_division=0))

    print("\n=== Done ===\n")


if __name__ == "__main__":
    main()
