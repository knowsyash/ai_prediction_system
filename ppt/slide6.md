# Web Scraping Methodology & Data Pipeline

## Scraping Architecture
* **Core Technologies:** Built using Python, leveraging `Requests` for HTTP calls and `BeautifulSoup` for HTML parsing and DOM traversal (targeting Flipkart).
* **Robustness & Anti-Bot Mechanisms:**
  * **User-Agent Rotation:** Cycles through various browser headers to simulate real user traffic and bypass basic bot detection.
  * **Request Throttling:** Introduces randomized delays between page requests to prevent server overloading and mitigate IP bans.
  * **Resilience:** Implements retry logic with exponential backoff to recover gracefully from temporary network errors.

## Logging & Data Storage
* **State Management:** The scraper maintains continuous text logs (e.g., `simple_save.txt`) to record the exact page progress and capture any runtime errors. This allows the system to pause and safely resume interrupted scrapes without data loss.
* **Dataset Export:** Extracted DOM elements (Review Text, Rating, Reviewer Name, Date) are structured using `Pandas` DataFrames and saved directly as CSV files for the next stage.

## Transition to Preprocessing
* Raw CSVs are moved to the `2_dataset_final_folder` for immediate cleaning.
* Custom, rule-based NLP scripts (`clean_names.py`) automatically strip appended reviewer names and artifacts from the review text body, ensuring the sentiment analysis models only evaluate pure customer feedback.