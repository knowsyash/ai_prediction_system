# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
predict_next_month.py
=====================
Predict next-month rating for each device using:
  1. Linear trend on monthly mean ratings (from cleaned final dataset)
  2. Exponential smoothing (more weight to recent months)
  3. Sentiment signal from ensemble results (Soft Voting - best performer)
  4. Weighted ensemble of all three signals

Data sources:
  - 2_dataset_final_folder/*.csv          (cleaned reviews with dates)
  - 4_enemble_analysis/ensemble_results_v2.csv  (per-review ensemble scores)
  - 4_enemble_analysis/ensemble_summary_v2.csv  (method accuracy weights)

Outputs (in 5_next_month/):
  next_month_prediction_v2.csv   -- final predictions table
  monthly_trend_<device>.png     -- time series + forecast per device
  prediction_summary.png         -- side-by-side bar chart of all predictions
"""

import os
import re
import math
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
HERE         = os.path.dirname(os.path.abspath(__file__))
ROOT         = os.path.normpath(os.path.join(HERE, ".."))
DATA_DIR     = os.path.join(ROOT, "2_dataset_final_folder")
ENSEMBLE_CSV = os.path.join(ROOT, "4_enemble_analysis", "ensemble_results_v2.csv")
SUMMARY_CSV  = os.path.join(ROOT, "4_enemble_analysis", "ensemble_summary_v2.csv")
OUT_DIR      = HERE

DATASETS = {
    "iPhone 16": os.path.join(DATA_DIR, "iphone16.csv"),
    "iPhone 15": os.path.join(DATA_DIR, "iphone15.csv"),
    "iQOO Z10":  os.path.join(DATA_DIR, "iqoo_z10.csv"),
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
MONTH_MAP = {
    "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
    "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12
}

def parse_month(val):
    """Parse 'Nov 2025' -> pd.Timestamp(2025-11-01). Returns NaT on failure."""
    if not isinstance(val, str):
        return pd.NaT
    val = val.strip()
    m = re.match(r"^([A-Za-z]{3})\s+(\d{4})$", val)
    if m:
        mon = MONTH_MAP.get(m.group(1).lower())
        yr  = int(m.group(2))
        if mon and 2000 <= yr <= 2100:
            return pd.Timestamp(yr, mon, 1)
    return pd.NaT


def month_str(ts):
    return ts.strftime("%b %Y")


def next_month(ts):
    if ts.month == 12:
        return pd.Timestamp(ts.year + 1, 1, 1)
    return pd.Timestamp(ts.year, ts.month + 1, 1)


def linear_trend(values, n_ahead=1):
    """Linear regression forecast n_ahead steps ahead. Returns (pred, residual_std)."""
    n = len(values)
    x = np.arange(n, dtype=float)
    if n < 2:
        return float(values[-1]), 0.0
    slope, intercept = np.polyfit(x, values.astype(float), 1)
    fitted = slope * x + intercept
    std    = float(np.std(values - fitted, ddof=0))
    pred   = float(slope * (n - 1 + n_ahead) + intercept)
    return pred, std


def exp_smooth_forecast(values, alpha=0.35):
    """Single exponential smoothing — last smoothed value is the forecast."""
    if len(values) == 0:
        return np.nan
    s = float(values[0])
    for v in values[1:]:
        s = alpha * float(v) + (1 - alpha) * s
    return s


def confidence_band(std, n_months, rmse_method):
    """
    95 % prediction interval half-width (simplified):
      = t * sqrt(MSE_model + sigma_data^2)
    We approximate using residual std and RMSE of the best ensemble model.
    """
    t = 2.0   # ~95% for reasonable n
    combined = math.sqrt(std**2 + rmse_method**2)
    # Widen band when fewer months available
    data_penalty = max(0, (6 - n_months) * 0.05)
    return round(t * combined + data_penalty, 3)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — BUILD MONTHLY SERIES FROM CLEANED DATASET
# ─────────────────────────────────────────────────────────────────────────────
def build_monthly(device, path):
    df = pd.read_csv(path)

    # rename text column if needed
    if "text" in df.columns and "review_text" not in df.columns:
        df = df.rename(columns={"text": "review_text"})

    df["ts"]     = df["date"].apply(parse_month)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["ts", "rating"])
    df["rating"] = df["rating"].clip(1, 5)
    df["is_pos"] = (df["rating"] >= 4).astype(int)

    monthly = (
        df.groupby("ts")
        .agg(
            n=("rating", "count"),
            mean_rating=("rating", "mean"),
            pct_positive=("is_pos", lambda x: x.mean() * 100),
        )
        .reset_index()
        .sort_values("ts")
        .reset_index(drop=True)
    )

    # Filter out stray months with tiny samples (< 5 reviews) UNLESS it's recent
    max_ts = monthly["ts"].max()
    monthly = monthly[
        (monthly["n"] >= 5) | (monthly["ts"] >= max_ts - pd.DateOffset(months=2))
    ].reset_index(drop=True)

    return monthly


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — LOAD SENTIMENT SIGNAL FROM ENSEMBLE
# ─────────────────────────────────────────────────────────────────────────────
def load_sentiment_signal():
    """
    Returns dict: {device -> avg soft_vote_pred_rating (1-5 scale)}
    Soft Voting chosen: best combined Accuracy + Pearson r.
    """
    if not os.path.exists(ENSEMBLE_CSV):
        print("  [WARN] ensemble_results_v2.csv not found — sentiment signal skipped.")
        return {}
    df = pd.read_csv(ENSEMBLE_CSV)
    signals = {}
    for dev in df["device"].unique():
        sub = df[df["device"] == dev]
        signals[dev] = round(float(sub["soft_vote_pred_rating"].mean()), 4)
    return signals


def load_ensemble_rmse():
    """Return RMSE of Soft Voting from ensemble summary (used for CI width)."""
    if not os.path.exists(SUMMARY_CSV):
        return 1.0
    df = pd.read_csv(SUMMARY_CSV)
    sv = df[df["Method"] == "Soft Voting"]
    if sv.empty:
        return 1.0
    return float(sv["RMSE"].iloc[0])


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — PREDICT NEXT MONTH PER DEVICE
# ─────────────────────────────────────────────────────────────────────────────
def predict_device(device, monthly, sentiment_signal, ensemble_rmse):
    """
    Weighted combination:
      w1 = 0.40 → Linear trend (captures direction)
      w2 = 0.35 → Exponential smoothing (weights recent data)
      w3 = 0.25 → Sentiment signal from ensemble (captures text sentiment)
    """
    n  = len(monthly)
    ratings = monthly["mean_rating"].to_numpy()
    last_ts = pd.Timestamp(monthly["ts"].max())
    target_ts = next_month(last_ts)

    # --- Signal 1: Linear trend
    lin_pred, lin_std = linear_trend(ratings)
    lin_pred = float(np.clip(lin_pred, 1.0, 5.0))

    # --- Signal 2: Exponential smoothing
    # Use alpha that adapts to dataset size (more data → trust trend more)
    alpha = 0.30 if n >= 8 else 0.45
    exp_pred = float(np.clip(exp_smooth_forecast(ratings, alpha=alpha), 1.0, 5.0))

    # --- Signal 3: Sentiment from ensemble (already on 1-5 scale)
    sent_pred = float(np.clip(sentiment_signal.get(device, np.mean(ratings)), 1.0, 5.0))

    # --- Weighted combination
    if n < 3:
        # Very little data — trust sentiment more
        w1, w2, w3 = 0.20, 0.30, 0.50
    elif n < 6:
        w1, w2, w3 = 0.30, 0.35, 0.35
    else:
        w1, w2, w3 = 0.40, 0.35, 0.25

    final_pred = w1 * lin_pred + w2 * exp_pred + w3 * sent_pred
    final_pred = float(np.clip(final_pred, 1.0, 5.0))

    # --- Confidence interval
    ci_half = confidence_band(lin_std, n, ensemble_rmse)
    ci_lo   = round(max(1.0, final_pred - ci_half), 3)
    ci_hi   = round(min(5.0, final_pred + ci_half), 3)

    # --- Sentiment category
    def label(r):
        if r >= 4.0: return "Positive"
        if r >= 3.0: return "Neutral"
        return "Negative"

    # --- Trend direction vs last observed month
    last_rating = float(ratings[-1])
    delta = final_pred - last_rating
    trend_arrow = "^" if delta > 0.05 else ("v" if delta < -0.05 else "-")

    # --- pct_positive forecast (simple exp smooth)
    pct_arr  = monthly["pct_positive"].to_numpy()
    pct_pred = float(np.clip(exp_smooth_forecast(pct_arr, alpha=alpha), 0, 100))

    # --- Confidence score (heuristic)
    raw_conf = 90 - lin_std * 20 - max(0, 5 - n) * 4
    conf_score = round(float(np.clip(raw_conf, 30, 95)), 1)

    return {
        "device":                    device,
        "target_month":              month_str(target_ts),
        "months_of_history":         int(n),
        "last_observed_month":       month_str(last_ts),
        "last_mean_rating":          round(last_rating, 3),
        "last_pct_positive":         round(float(monthly["pct_positive"].iloc[-1]), 1),
        # component predictions
        "linear_trend_pred":         round(lin_pred,   3),
        "exp_smooth_pred":           round(exp_pred,   3),
        "sentiment_signal_pred":     round(sent_pred,  3),
        # weights used
        "w_linear":                  w1,
        "w_exp_smooth":              w2,
        "w_sentiment":               w3,
        # final
        "predicted_rating":          round(final_pred, 3),
        "predicted_pct_positive":    round(pct_pred, 1),
        "ci_lower":                  ci_lo,
        "ci_upper":                  ci_hi,
        "sentiment_label":           label(final_pred),
        "trend_vs_last":             trend_arrow,
        "delta_vs_last":             round(delta, 3),
        "confidence_score":          conf_score,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — PLOTS
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    "iPhone 15": "#4C72B0",
    "iPhone 16": "#55A868",
    "iQOO Z10":  "#DD8452",
}

def plot_monthly_trend(device, monthly, result):
    """Line plot of historical monthly mean rating + forecast point with CI."""
    fig, ax = plt.subplots(figsize=(10, 5))
    color = COLORS.get(device, "#333")

    xs = list(range(len(monthly)))
    ys = monthly["mean_rating"].tolist()
    ns = monthly["n"].tolist()

    # Historical line
    ax.plot(xs, ys, marker="o", color=color, linewidth=2, markersize=6, label="Observed")

    # Annotate each month
    for i, (x, y, n) in enumerate(zip(xs, ys, ns)):
        ax.annotate(f"{y:.2f}\n(n={n})", (x, y),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=7, color="#444")

    # Forecast point
    fx = len(monthly)
    fy = result["predicted_rating"]
    ci_lo = result["ci_lower"]
    ci_hi = result["ci_upper"]

    ax.errorbar(fx, fy, yerr=[[fy - ci_lo], [ci_hi - fy]],
                fmt="D", color="crimson", markersize=9, capsize=6,
                linewidth=2, label=f"Forecast {result['target_month']}\n"
                                   f"={fy:.3f} [{ci_lo}–{ci_hi}]")

    # Dashed connector
    ax.plot([fx - 1, fx], [ys[-1], fy], "--", color="crimson", alpha=0.5)

    # X-axis labels
    labels = [month_str(ts) for ts in monthly["ts"]] + [result["target_month"]]
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.set_ylim(1, 5.5)
    ax.set_ylabel("Mean Rating (1–5)", fontsize=11)
    ax.set_title(
        f"{device} — Monthly Rating Trend & Next-Month Forecast\n"
        f"Sentiment signal: {result['sentiment_signal_pred']:.3f} | "
        f"Confidence: {result['confidence_score']}%",
        fontsize=12
    )
    ax.legend(fontsize=9, loc="lower left")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    safe = device.replace(" ", "_").replace("/", "_")
    fname = os.path.join(OUT_DIR, f"trend_{safe}_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


def plot_summary(results):
    """Side-by-side grouped bar chart: last observed vs predicted rating."""
    devices = [r["device"] for r in results]
    last    = [r["last_mean_rating"]  for r in results]
    pred    = [r["predicted_rating"]  for r in results]
    ci_lo   = [r["ci_lower"]          for r in results]
    ci_hi   = [r["ci_upper"]          for r in results]
    err_lo  = [p - lo for p, lo in zip(pred, ci_lo)]
    err_hi  = [hi - p for p, hi in zip(pred, ci_hi)]
    months  = [r["target_month"]      for r in results]

    x      = np.arange(len(devices))
    width  = 0.32
    colors = [COLORS.get(d, "#888") for d in devices]

    fig, ax = plt.subplots(figsize=(10, 6))

    # Last observed
    bars1 = ax.bar(x - width/2, last, width, label="Last Observed",
                   color=colors, alpha=0.5, edgecolor="white", hatch="//")
    # Predicted
    bars2 = ax.bar(x + width/2, pred, width, label="Predicted (next month)",
                   color=colors, alpha=0.92, edgecolor="white")
    # CI error bars on predicted
    ax.errorbar(x + width/2, pred,
                yerr=[err_lo, err_hi],
                fmt="none", color="black", capsize=6, linewidth=1.5)

    # Annotate
    for bar, v in zip(bars1, last):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.04,
                f"{v:.2f}", ha="center", va="bottom", fontsize=9, color="#555")
    for bar, v, m in zip(bars2, pred, months):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.04,
                f"{v:.3f}\n{m}", ha="center", va="bottom", fontsize=8.5,
                fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(devices, fontsize=11)
    ax.set_ylim(0, 6.0)
    ax.set_ylabel("Mean Rating (1–5)", fontsize=11)
    ax.set_title(
        "Next-Month Rating Prediction per Device\n"
        "(Weighted: Linear Trend + Exp Smoothing + Ensemble Sentiment)",
        fontsize=12
    )
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    # Trend arrows
    for i, r in enumerate(results):
        arrow = r["trend_vs_last"]
        color = "green" if arrow == "^" else ("red" if arrow == "v" else "gray")
        ax.text(x[i], 0.25, arrow, ha="center", fontsize=18,
                color=color, fontweight="bold")

    plt.tight_layout()
    fname = os.path.join(OUT_DIR, "prediction_summary_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


def plot_component_breakdown(results):
    """Stacked breakdown of the 3 prediction signals per device."""
    fig, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 5), sharey=True)
    if len(results) == 1:
        axes = [axes]

    component_labels = ["Linear Trend", "Exp Smoothing", "Sentiment"]
    component_keys   = ["linear_trend_pred", "exp_smooth_pred", "sentiment_signal_pred"]
    weight_keys      = ["w_linear", "w_exp_smooth", "w_sentiment"]
    comp_colors      = ["#4C72B0", "#55A868", "#DD8452"]

    for ax, r in zip(axes, results):
        device = r["device"]
        vals   = [r[k] for k in component_keys]
        ws     = [r[k] for k in weight_keys]
        final  = r["predicted_rating"]

        bars = ax.bar(component_labels, vals, color=comp_colors, alpha=0.85, edgecolor="white")
        for bar, v, w in zip(bars, vals, ws):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.05,
                    f"{v:.3f}\n(w={w:.0%})", ha="center", va="bottom", fontsize=8.5)

        ax.axhline(final, color="crimson", linestyle="--", linewidth=2,
                   label=f"Final pred = {final:.3f}")
        ax.axhline(r["last_mean_rating"], color="gray", linestyle=":",
                   linewidth=1.5, label=f"Last obs = {r['last_mean_rating']:.3f}")
        ax.set_ylim(1, 5.8)
        ax.set_title(f"{device}\n→ {r['target_month']}", fontsize=11)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        plt.setp(ax.get_xticklabels(), rotation=15, ha="right", fontsize=9)

    fig.suptitle("Prediction Component Breakdown per Device", fontsize=13)
    plt.tight_layout()
    fname = os.path.join(OUT_DIR, "component_breakdown_v2.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"  Saved: {os.path.basename(fname)}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n=== Next-Month Rating Predictor (v2 — Sentiment-Augmented) ===\n")

    # Load sentiment & RMSE from ensemble
    print("[1] Loading ensemble sentiment signals ...")
    sentiment = load_sentiment_signal()
    rmse      = load_ensemble_rmse()
    print(f"  Soft Voting RMSE (used for CI): {rmse}")
    for dev, sig in sentiment.items():
        print(f"  {dev}: avg sentiment predicted rating = {sig:.4f}")
    print()

    results = []

    print("[2] Building monthly series & predicting per device ...")
    for device, path in DATASETS.items():
        if not os.path.exists(path):
            print(f"  [SKIP] {device}: file not found")
            continue
        monthly = build_monthly(device, path)
        if monthly.empty:
            print(f"  [SKIP] {device}: no usable date data")
            continue
        n = len(monthly)
        print(f"  {device}: {n} months of data "
              f"({month_str(monthly['ts'].min())} – {month_str(monthly['ts'].max())})")
        result = predict_device(device, monthly, sentiment, rmse)
        results.append((device, monthly, result))

    print()

    # Print predictions
    print("=" * 70)
    print("  NEXT-MONTH PREDICTIONS")
    print("=" * 70)
    for device, _, r in results:
        print(f"\n  {device}  →  {r['target_month']}")
        print(f"    Predicted rating    : {r['predicted_rating']:.3f} "
              f"[{r['ci_lower']} – {r['ci_upper']}]  {r['trend_vs_last']}")
        print(f"    Predicted % positive: {r['predicted_pct_positive']:.1f}%")
        print(f"    Sentiment label     : {r['sentiment_label']}")
        print(f"    Confidence score    : {r['confidence_score']}%")
        print(f"    Components          : "
              f"Linear={r['linear_trend_pred']:.3f} (w={r['w_linear']:.0%}), "
              f"ExpSmooth={r['exp_smooth_pred']:.3f} (w={r['w_exp_smooth']:.0%}), "
              f"Sentiment={r['sentiment_signal_pred']:.3f} (w={r['w_sentiment']:.0%})")

    # Save CSV
    out_rows = [r for _, _, r in results]
    out_df   = pd.DataFrame(out_rows)
    csv_path = os.path.join(OUT_DIR, "next_month_prediction_v2.csv")
    out_df.to_csv(csv_path, index=False)
    print(f"\n  CSV saved -> {os.path.basename(csv_path)}")

    # Plots
    print("\n[3] Generating plots ...")
    for device, monthly, result in results:
        plot_monthly_trend(device, monthly, result)
    plot_summary([r for _, _, r in results])
    plot_component_breakdown([r for _, _, r in results])

    print("\n=== Done ===\n")


if __name__ == "__main__":
    main()
