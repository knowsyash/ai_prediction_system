
# AI-Powered Predictive Analysis of Smartphone Market Trends

**Version 2.0 - Last Updated: 2026-04-28**

## Introduction

This document provides a comprehensive analysis of the AI Prediction System, a project designed to forecast future market trends for smartphones based on public sentiment. By scraping and analyzing customer reviews from e-commerce platforms, the system employs a multi-stage pipeline involving data scraping, cleaning, sentiment analysis, and predictive modeling to generate actionable insights.

This report details each stage of the pipeline, from initial data acquisition to the final prediction of next-month product ratings. It covers the methodologies, technologies, and results of each component, offering a complete technical overview of the system.

---

## 1. Data Scraping

**Folder:** `1_data_scrapping/`

The foundation of our predictive system is the automated collection of customer reviews. This phase focuses on systematically gathering raw data from the web.

### 1.1. Methodology

The scraping process targets Flipkart product pages for various smartphones, including the iPhone 15, iPhone 16, and iQOO Z10. A Python script, `simple_scraper.py`, is used to navigate through review pages and extract relevant information.

The scraper is designed to be robust and respectful to the host server:
- **User-Agent Rotation:** It cycles through a list of common user-agent strings to mimic different browsers and avoid being blocked.
- **Request Throttling:** Random delays are introduced between requests to prevent overloading the server.
- **Error Handling:** The script includes retry logic with exponential backoff to handle network errors or temporary server issues.
- **Progress Tracking:** It maintains a log file (`simple_save.txt`) to record its progress and any errors encountered, allowing for easy monitoring and resumption of interrupted scrapes.

### 1.2. Technology Stack

- **Python:** The core language for the scraper.
- **Requests:** A powerful and simple HTTP library for making web requests.
- **BeautifulSoup:** A library for parsing HTML and XML documents, used to navigate the HTML structure of the review pages and extract data.
- **Pandas:** Used to structure the scraped data into a DataFrame and save it to a CSV file.

### 1.3. Output

The output of the scraping process is a set of CSV files, one for each product:
- `iphone15_reviews.csv`
- `iphone16_reviews.csv`
- `iqoo_z10_reviews.csv`

Each CSV file contains the following columns:
- **rating:** The star rating given by the user (1-5).
- **text:** The full text of the review.
- **name:** The name of the reviewer.
- **date:** The date the review was posted.

These files serve as the raw input for the next stage of the pipeline.

---

## 2. Data Cleaning and Preparation

**Folder:** `2_dataset_final_folder/`

Raw scraped data is often noisy and requires cleaning to be useful for analysis. This stage focuses on preprocessing the review text to improve the quality of the data.

### 2.1. Methodology

The primary cleaning task is to remove reviewer names that are often appended to the end of the review text. The `clean_names.py` script is designed for this purpose.

The script uses a conservative, rule-based approach to identify and remove names:
- It looks for two or three-word phrases at the end of the review text.
- It checks if these words are common English words using a large, predefined dictionary. If they are not common words, they are more likely to be a name.
- It also checks for punctuation or the presence of content words before the potential name to avoid incorrectly removing parts of the review.

This process ensures that the review text contains only the customer's opinion, which is crucial for accurate sentiment analysis.

### 2.2. Output

This folder contains both the original and cleaned datasets:
- `iphone15_before_name_clean.csv`, `iphone16_before_name_clean.csv`, `iqoo_z10_before_name_clean.csv`: Backups of the raw data before name cleaning.
- `iphone15.csv`, `iphone16.csv`, `iqoo_z10.csv`: The final, cleaned datasets that are used for all subsequent analysis.

---

## 3. Sentiment Analysis

**Folder:** `3_sentimental_analysis/`

With clean data, the next step is to quantify the sentiment expressed in each review. This folder contains scripts and notebooks for comparing different sentiment analysis techniques.

### 3.1. Methodology

The `compare_methods_v2.py` script evaluates three distinct approaches to sentiment analysis:

1.  **VADER (Valence Aware Dictionary and sEntiment Reasoner):** A lexicon and rule-based sentiment analysis tool that is specifically attuned to sentiments expressed in social media. It is fast and does not require any training.
2.  **BERT (Bidirectional Encoder Representations from Transformers):** A state-of-the-art, pre-trained deep learning model. We use a fine-tuned version for sentiment analysis from the `transformers` library. This method is more computationally intensive but can capture more nuanced sentiment.
3.  **Word Cloud Category Proxy:** A custom TF-IDF-based keyword scoring method. It identifies positive and negative keywords and scores the review based on the presence and frequency of these words.

The performance of these methods is evaluated against the ground truth of the star ratings.

### 3.2. Metrics and Results

The following metrics are used to compare the models:
- **Pearson and Spearman Correlation:** To measure the linear and monotonic relationship between the predicted sentiment and the actual star rating.
- **Root Mean Squared Error (RMSE):** To measure the average difference between the predicted and actual ratings on a 1-5 scale.
- **Accuracy and Macro-F1 Score:** To evaluate the performance on a 3-class classification task (Positive, Neutral, Negative).

The results are saved in `comparison_summary_v2.csv`. Typically, BERT-based models outperform lexicon-based methods like VADER in capturing nuanced sentiment, though at a higher computational cost. The Word Cloud method provides a simple, interpretable baseline.

---

## 4. Ensemble Analysis

**Folder:** `4_enemble_analysis/`

To improve the accuracy and robustness of our sentiment predictions, we use ensemble methods to combine the outputs of the individual models.

### 4.1. Methodology

The `ensemble_analysis.py` script implements several ensemble techniques:

1.  **Hard Voting:** A simple majority vote. The final sentiment label is the one predicted by the majority of the models.
2.  **Soft Voting:** The final prediction is based on the average of the predicted probabilities (or scores) from each model. This method often performs better as it takes into account the confidence of each model.
3.  **Bagging (Bootstrap Aggregating):** This method involves creating multiple bootstrap samples of the data, training a model on each, and then aggregating the predictions. This helps to reduce variance and improve stability.

### 4.2. Results

The results of the ensemble analysis are stored in `ensemble_summary_v2.csv`. Ensemble methods, particularly Soft Voting and Bagging, consistently outperform any single model. This is because they leverage the strengths of different models and reduce the impact of individual model errors.

The `ensemble_results_v2.csv` file contains the detailed predictions for each review, which are then used to calculate a more reliable cumulative rating for each product.

---

## 5. Next Month Prediction

**Folder:** `5_next_month/`

The final stage of the pipeline is to use the analyzed sentiment to predict future product performance.

### 5.1. Methodology

The `predict_next_month.py` script uses a weighted ensemble of three signals to forecast the next-month average rating for each device:

1.  **Linear Trend:** A linear regression model is fitted to the historical monthly average ratings to project the trend into the next month.
2.  **Exponential Smoothing:** This method gives more weight to recent data, making it more responsive to recent changes in sentiment.
3.  **Sentiment Signal:** The sentiment scores from the best-performing ensemble model (Soft Voting) are used as a leading indicator of future ratings.

These three signals are combined using weights derived from their historical accuracy, creating a final, robust prediction.

### 5.2. Output

The final predictions are saved in `next_month_prediction_v2.csv`. This file provides a clear, data-driven forecast of the expected performance of each product in the upcoming month. The folder also contains visualizations of the trends and predictions:

- `trend_<device>_v2.png`: Shows the historical monthly ratings and the forecasted trend for each device.
- `prediction_summary_v2.png`: A bar chart comparing the final predictions for all devices.

This predictive insight is the ultimate output of the AI Prediction System, providing valuable information for market analysis and business strategy.
