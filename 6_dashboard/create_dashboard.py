"""
create_dashboard.py
=====================
Generates an interactive dashboard to visualize the project's results.

- Replicates the monthly time-series aggregation from the prediction script.
- Compares individual and ensemble model performance with charts.
- Displays final next-month predictions and their component breakdown.
- Shows historical and predicted time-series data with confidence intervals.
"""

import os
import re
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# --- 1. Paths and Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))

DATA_DIR = os.path.join(ROOT_DIR, "2_dataset_final_folder")
SENTIMENT_SUMMARY_PATH = os.path.join(ROOT_DIR, "3_sentimental_analysis/YS/comparison_summary_v2.csv")
ENSEMBLE_SUMMARY_PATH = os.path.join(ROOT_DIR, "4_enemble_analysis/ensemble_summary_v2.csv")
NEXT_MONTH_PRED_PATH = os.path.join(ROOT_DIR, "5_next_month/next_month_prediction_v2.csv")
ENSEMBLE_RESULTS_PATH = os.path.join(ROOT_DIR, "4_enemble_analysis/ensemble_results_v2.csv")

DATASETS = {
    "iPhone 16": os.path.join(DATA_DIR, "iphone16.csv"),
    "iPhone 15": os.path.join(DATA_DIR, "iphone15.csv"),
    "iQOO Z10":  os.path.join(DATA_DIR, "iqoo_z10.csv"),
}

MONTH_MAP = {
    "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
    "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12
}

# --- 2. Data Loading and Processing Functions ---

def parse_month(val):
    if not isinstance(val, str): return pd.NaT
    m = re.match(r"^([A-Za-z]{3})\s+(\d{4})$", val.strip())
    if m:
        mon, yr = MONTH_MAP.get(m.group(1).lower()), int(m.group(2))
        if mon and 2000 <= yr <= 2100: return pd.Timestamp(yr, mon, 1)
    return pd.NaT

def build_monthly(device, path):
    df = pd.read_csv(path)
    if "text" in df.columns and "review_text" not in df.columns:
        df = df.rename(columns={"text": "review_text"})
    df["ts"] = df["date"].apply(parse_month)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").clip(1, 5)
    df = df.dropna(subset=["ts", "rating"])
    monthly = df.groupby("ts").agg(Actual_Rating=("rating", "mean")).reset_index()
    monthly['Device'] = device
    return monthly

# --- 3. Load All Data ---

sentiment_summary_df = pd.read_csv(SENTIMENT_SUMMARY_PATH)
ensemble_summary_df = pd.read_csv(ENSEMBLE_SUMMARY_PATH)
next_month_pred_df = pd.read_csv(NEXT_MONTH_PRED_PATH)

review_dfs = [pd.read_csv(path).rename(columns={"text": "review_text"}) for path in DATASETS.values()]
all_reviews_df = pd.concat(review_dfs)[['review_text', 'date']].dropna()

all_devices_monthly_df = pd.concat([build_monthly(dev, p) for dev, p in DATASETS.items()]).rename(columns={'ts': 'Date'})

ensemble_results_df = pd.read_csv(ENSEMBLE_RESULTS_PATH)
ensemble_results_df = pd.merge(ensemble_results_df, all_reviews_df, on='review_text', how='left')
ensemble_results_df['Date'] = ensemble_results_df['date'].apply(parse_month)

monthly_preds_df = ensemble_results_df.groupby(['device', 'Date']).agg(
    Soft_Voting_Pred_Rating=('soft_vote_pred_rating', 'mean')
).reset_index().rename(columns={'device': 'Device'})

time_series_df = pd.merge(all_devices_monthly_df, monthly_preds_df, on=['Device', 'Date'], how='left')

# --- 4. Prepare Data for Visualization ---

# For performance charts
perf_df = pd.concat([
    sentiment_summary_df[['Method', 'Macro_F1', 'RMSE']],
    ensemble_summary_df[['Method', 'Macro_F1', 'RMSE']]
]).reset_index(drop=True)

# For prediction breakdown
pred_breakdown_df = next_month_pred_df[[
    'device', 'linear_trend_pred', 'exp_smooth_pred', 'sentiment_signal_pred',
    'w_linear', 'w_exp_smooth', 'w_sentiment'
]].copy()
pred_breakdown_df['linear_contrib'] = pred_breakdown_df['linear_trend_pred'] * pred_breakdown_df['w_linear']
pred_breakdown_df['exp_smooth_contrib'] = pred_breakdown_df['exp_smooth_pred'] * pred_breakdown_df['w_exp_smooth']
pred_breakdown_df['sentiment_contrib'] = pred_breakdown_df['sentiment_signal_pred'] * pred_breakdown_df['w_sentiment']

# For time series with confidence interval
next_month_pred_df['target_month_ts'] = next_month_pred_df['target_month'].apply(parse_month)
ci_df = next_month_pred_df[['device', 'target_month_ts', 'predicted_rating', 'ci_lower', 'ci_upper']].rename(
    columns={'device': 'Device', 'target_month_ts': 'Date', 'predicted_rating': 'Soft_Voting_Pred_Rating'}
)

# --- 5. Initialize and Layout Dash App ---
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.title = "AI Prediction System Dashboard"

app.layout = html.Div(children=[
    html.H1('AI Prediction System: Final Results Dashboard', style={'textAlign': 'center'}),

    html.H3('1. Final Next-Month Forecast Breakdown', style={'marginTop': 40}),
    dcc.Dropdown(
        id='device-breakdown-dropdown',
        options=[{'label': dev, 'value': dev} for dev in pred_breakdown_df['device'].unique()],
        value=pred_breakdown_df['device'].unique()[0], style={'width': '50%', 'margin': 'auto'}
    ),
    dcc.Graph(id='prediction-breakdown-chart'),

    html.H3('2. Historical and Predicted Ratings Trend', style={'marginTop': 40}),
    dcc.Dropdown(
        id='device-timeseries-dropdown',
        options=[{'label': dev, 'value': dev} for dev in time_series_df['Device'].unique()],
        value=time_series_df['Device'].unique()[0], style={'width': '50%', 'margin': 'auto'}
    ),
    dcc.Graph(id='ratings-time-series-chart')
])

# --- 6. Callbacks for Interactivity ---

@app.callback(Output('prediction-breakdown-chart', 'figure'), [Input('device-breakdown-dropdown', 'value')])
def update_breakdown_chart(device):
    dev_data = pred_breakdown_df[pred_breakdown_df['device'] == device].iloc[0]
    total_pred = dev_data[['linear_contrib', 'exp_smooth_contrib', 'sentiment_contrib']].sum()
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Component</b>', '<b>Value</b>', '<b>Weight</b>', '<b>Contribution</b>'],
            fill_color='royalblue',
            font=dict(color='white', size=14),
            align='left'
        ),
        cells=dict(
            values=[
                ['Linear Trend', 'Exp. Smoothing', 'Sentiment Signal', '<b>Final Prediction</b>'],
                [f"{dev_data['linear_trend_pred']:.3f}", f"{dev_data['exp_smooth_pred']:.3f}", f"{dev_data['sentiment_signal_pred']:.3f}", "-"],
                [f"{dev_data['w_linear']:.3f}", f"{dev_data['w_exp_smooth']:.3f}", f"{dev_data['w_sentiment']:.3f}", "-"],
                [f"{dev_data['linear_contrib']:.3f}", f"{dev_data['exp_smooth_contrib']:.3f}", f"{dev_data['sentiment_contrib']:.3f}", f"<b>{total_pred:.3f}</b>"]
            ],
            fill_color=['lavender', 'white', 'white', 'white'],
            align='left',
            font=dict(size=13)
        )
    )])
    fig.update_layout(title=f'Forecast Breakdown for {device}', margin=dict(t=50, l=20, r=20, b=20))
    return fig

@app.callback(Output('ratings-time-series-chart', 'figure'), [Input('device-timeseries-dropdown', 'value')])
def update_time_series_chart(device):
    dev_ts = time_series_df[time_series_df['Device'] == device]
    dev_ci = ci_df[ci_df['Device'] == device]

    fig = go.Figure()
    # Actual ratings
    fig.add_trace(go.Scatter(x=dev_ts['Date'], y=dev_ts['Actual_Rating'], mode='lines+markers', name='Actual Monthly Rating'))
    # Predicted ratings
    fig.add_trace(go.Scatter(x=dev_ts['Date'], y=dev_ts['Soft_Voting_Pred_Rating'], mode='lines+markers', name='Predicted (Soft Voting)'))
    
    # Next month prediction with CI
    fig.add_trace(go.Scatter(x=dev_ci['Date'], y=dev_ci['ci_upper'], mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=dev_ci['Date'], y=dev_ci['ci_lower'], mode='lines', line=dict(width=0),
                             fill='tonexty', fillcolor='rgba(255, 0, 0, 0.2)', name='95% Confidence Interval'))
    fig.add_trace(go.Scatter(x=dev_ci['Date'], y=dev_ci['Soft_Voting_Pred_Rating'], mode='markers',
                             marker=dict(color='red', size=10), name='Next Month Forecast'))

    fig.update_layout(title=f'Monthly Ratings Trend for {device}',
                      xaxis_title='Date', yaxis_title='Average Monthly Rating (1-5 Scale)',
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

# --- 7. Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
