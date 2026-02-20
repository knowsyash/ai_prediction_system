# Scraper Code Walkthrough — Line-by-Line Technical Documentation

**Three scrapers. Three different architectures. One goal: collect smartphone reviews.**

This document walks through every meaningful line of all three scrapers used in this project, explaining **what it does**, **why it was written that way**, and **how it works internally**.

---

## Table of Contents

1. [Scraper 1 — iPhone 15 / iPhone 16 (Flipkart, Page-based)](#scraper-1--iphone-15--iphone-16-flipkart-page-based)
2. [Scraper 2 — iQOO Z10 (Flipkart, Dual-Strategy)](#scraper-2--iqoo-z10-flipkart-dual-strategy)
3. [Scraper 3 — iPhone 14 Amazon (curl_cffi + Cookie Auth)](#scraper-3--iphone-14-amazon-curl_cffi--cookie-auth)
4. [Scraper 4 — iPhone 14 Flipkart (curl_cffi Single Fetch)](#scraper-4--iphone-14-flipkart-curl_cffi-single-fetch)
5. [Comparison: Why Each Scraper Is Different](#comparison-why-each-scraper-is-different)

---

## Scraper 1 — iPhone 15 / iPhone 16 (Flipkart, Page-based)

**File:** `data_scrapping/iphone15/simple_scraper.py`  
**Lines:** 502  
**Technique:** Standard `requests` + `BeautifulSoup`, multi-UA rotation, checkpoint resume, exponential backoff

---

### Part 1 — Imports and Class Setup

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime
```

| Import | Why it's here |
|--------|--------------|
| `requests` | Makes HTTP GET calls to Flipkart pages |
| `BeautifulSoup` | Parses the HTML string into a traversable tree |
| `pandas` | Reads/writes CSV, runs `.drop_duplicates()` |
| `time` | `time.sleep()` — adds deliberate delays between requests |
| `random` | `random.uniform()` — randomises delay intervals to look human |
| `re` | Regex for date parsing, city extraction, name removal |
| `datetime` | Timestamps log entries and calculates relative dates |

---

### Part 2 — Class Constants

```python
class SimpleFlipkartScraper:
    CSV_FILENAME = 'iphone15_reviews.csv'
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
```

**Why 5 different User-Agents?**

The `User-Agent` header tells the server what browser is making the request. Python's default `requests` sends `python-requests/2.x.x` which is immediately identifiable as a bot. By cycling through real Chrome/Firefox UAs, each request appears to come from a different browser instance.

The list includes:
- Chrome on Windows (most common globally)
- Chrome on macOS  
- Chrome on Linux
- Firefox on Windows — UAs are rotated with `(self.current_ua_index + 1) % len(self.USER_AGENTS)` so they go in order rather than randomly, ensuring every UA gets equal use.

---

### Part 3 — `__init__` : Initialisation

```python
def __init__(self):
    self.session = requests.Session()       # (A)
    self.current_ua_index = 0              # (B)
    self.reviews = []                      # (C)
    self.progress_file = 'simple_save.txt' # (D)
    self.last_successful_page = None       # (E)
    self.consecutive_empty = 0             # (F)
    self.total_in_file = self._count_existing_reviews()  # (G)
    self.network_errors = 0               # (H)
```

**(A) `requests.Session()`** — A Session object persists cookies and TCP connections across multiple requests to the same host. Without it, every `requests.get()` creates a fresh TCP socket and TLS handshake (~200ms overhead per page). The Session reuses the same connection (HTTP keep-alive), reducing that to ~10ms. It also **automatically stores and replays cookies** — when Flipkart sets a session cookie on request 1, it is automatically sent on requests 2, 3, 4... exactly like a browser does.

**(C) `self.reviews = []`** — In-memory buffer. Reviews collected in the current 5-page batch are stored here before being flushed to CSV at each checkpoint. This avoids opening and writing the CSV file for every single review (disk I/O is slow).

**(D) `'simple_save.txt'`** — Human-readable log file. Every page's result is appended with a timestamp. This serves double duty: debugging + progress tracking.

**(F) `self.consecutive_empty = 0`** — Counter for how many pages in a row returned zero reviews. If this reaches 5, the scraper stops. This handles the end of the review list gracefully — Flipkart doesn't send a "no more pages" signal; you just get empty pages.

**(G) `self._count_existing_reviews()`** — Reads the existing CSV and counts rows. Lets the scraper know on startup how much data is already collected.

**(H) `self.network_errors = 0`** — Tracks consecutive network failures. After 10 errors, triggers a 5-minute cooldown to avoid aggressive retries during server issues.

---

### Part 4 — Text Cleaning

```python
def _extract_and_format_date(self, text):
    # First: look for explicit "Oct, 2024" or "Jan 2025"
    actual_date_pattern = re.search(
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+(\d{4})',
        text, re.IGNORECASE
    )
    if actual_date_pattern:
        return f"{actual_date_pattern.group(1)} {actual_date_pattern.group(2)}"
    
    # Second: look for relative "3 months ago"
    month_pattern = re.search(r'(\d+)\s*months?\s*ago', text, re.IGNORECASE)
    ...
    current_date = datetime.now()
    if month_pattern:
        months = int(month_pattern.group(1))
        review_date = current_date - relativedelta(months=months)  # (A)
```

**(A) `relativedelta`** from `python-dateutil` — handles calendar arithmetic correctly. Regular `timedelta` only works in days. `relativedelta(months=3)` correctly subtracts 3 calendar months (accounts for different month lengths: Feb has 28 days, etc.). `datetime.now() - relativedelta(months=3)` on 2026-02-10 gives 2025-11-10.

Flipkart shows dates in two formats:
- **Absolute:** `"Oct, 2024"` (when review is old enough)
- **Relative:** `"3 months ago"` (when review is recent)

The code tries absolute first (more precise), falls back to relative.

---

### Part 6 — City Extraction

```python
def _extract_city(self, text):
    text = re.sub(r'\d{10,}', '', text)   # (A) remove phone numbers first
    
    # Pattern 1: ", Palakkad District" or ", Kochi" at end
    city_match = re.search(
        r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:District|Division|City))?)[\s,]*$',
        text
    )
```

**(A)** Flipkart sometimes shows reviewer phone numbers in the text (rare). `\d{10,}` matches any sequence of 10+ digits and removes it before city detection, otherwise the phone number confuses the city regex.

**The city regex explained character by character:**
```
,\s*                 → literal comma, then 0+ whitespace
(                    → start capture group
  [A-Z][a-z]+        → word starting with uppercase: "Mumbai"
  (?:\s+[A-Z][a-z]+)*  → 0+ more capitalized words: " New Delhi" → "New", "Delhi"
  (?:\s+             → optional suffix:
    (?:District|Division|City)
  )?
)                    → end capture group
[\s,]*$              → trailing whitespace/comma to end of string
```

This matches: `", Mumbai"`, `", New Delhi"`, `", Palakkad District"` but NOT `", great phone"` (lowercase g).

The **three-pattern fallback** handles Flipkart's inconsistent formatting:
1. City at absolute end of string
2. City before a month abbreviation (e.g. `", Delhi Oct 2024"`)
3. City anywhere with comma preceding it

---

### Part 7 — Text Cleaning

```python
def clean_text(self, text, remove_dates=True):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)   # (A) remove non-ASCII/emojis
    text = re.sub(r'\s+', ' ', text)              # (B) collapse whitespace
    text = re.sub(r'[^\w\s.,!?-]', '', text)      # (C) keep only safe chars
    text = re.sub(r'\b\d{10,}\b', '', text)        # (D) phone numbers
    
    # AGGRESSIVE NAME REMOVAL
    # 1. "FirstName LastName , City" pattern
    text = re.sub(
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\s*,\s*[A-Z][a-z]+...',
        '', text
    )
    # 2. "FirstName LastName" anywhere
    text = re.sub(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', '', text)
    # 3. ALL CAPS names
    text = re.sub(r'\b[A-Z][A-Z]+(?:\s+[A-Z]+)*\b', '', text)
```

**(A) `[^\x00-\x7F]`** — Matches any character outside the ASCII range (0–127). This removes:
- Emoji (unicode range 0x1F600+)
- Hindi/Tamil/regional script accidentally included
- Special Unicode quotes `"` `"` → replaced with space

**(B)** After emoji removal, you often get multiple spaces. `\s+` → `' '` collapses them back to single space.

**(C) `[^\w\s.,!?-]`** — Whitelist approach: keep only word characters (`\w` = letters, digits, `_`), whitespace, and basic punctuation (comma, period, exclamation, question mark, hyphen). Everything else (pipe `|`, tilde `~`, asterisk `*`, brackets) is removed.

**Why keep it simple?** This scraper focuses on extracting rating, title, and review text only. No date or city extraction needed for the analysis. The clean_text function ensures the data is readable and ML-ready without removing important content.

---

### Part 5 — Review Extraction Logic

The scraper uses a sophisticated multi-step process to identify and extract reviews from the page:

```python
# Extract title and review text with noise filtering
title_candidates = []
review_candidates = []

noise_keywords = ['Certified Buyer', 'Verified Purchase', 'Report Abuse', 
                 'Permalink', 'Helpful', 'READ MORE', 'Review for Color',
                 'Storage', 'ratings and', 'reviews']

for i, line in enumerate(lines[1:], 1):
    has_noise = any(kw in line for kw in noise_keywords)  # (A)
    if not has_noise and len(line) > 5:
        if i == 1 or (not title_candidates and len(line) < 100):  # (B)
            title_candidates.append(line)
        else:
            review_candidates.append(line)  # (C)

if title_candidates and review_candidates:
    title = self.clean_text(title_candidates[0])
    review_text = self.clean_text(' '.join(review_candidates))
    
    # Validate
    if (3 < len(title) < 150 and  # (D)
        15 < len(review_text) < 1000 and
        not title.replace(' ', '').replace(',', '').isdigit()):  # (E)
        
        review_key = f"{rating}_{title[:30]}_{review_text[:30]}"  # (F)
        if review_key not in seen_reviews:
            seen_reviews.add(review_key)
            page_reviews.append({
                'rating': int(rating),
                'title': title,
                'review_text': review_text
            })
```

**(A) Noise detection** — Flipkart injects UI elements (buttons, badges, metadata) into the review card HTML. Phrases like "Certified Buyer", "Report Abuse", "READ MORE" are filtered out. `any(kw in line for kw in noise_keywords)` checks if ANY keyword appears in the line.

**(B) Title identification** — The title is usually the first non-noise line after the rating, and typically shorter than 100 characters. If we haven't found a title yet and the line is short, it's likely the title.

**(C) Review body** — Everything after the title becomes part of the review body. Multiple lines are joined with spaces.

**(D) Validation rules:**
- Title: 3–150 characters (too short = metadata, too long = probably includes review text)
- Review text: 15–1000 characters (too short = spam, too long = truncate to avoid outliers)

**(E) Digit check** — Filters out lines that are purely numeric (ratings aggregates like "4.5, 3.2" that sometimes appear in the same div structure).

**(F) Deduplication key** — Uses a composite key of rating + first 30 chars of title + first 30 chars of review. This catches exact duplicates that might appear multiple times on the same page due to HTML structure overlap.

---

### Part 6 — Page Scraping Core

```python
def scrape_page(self, url):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()         # (A)
            self.network_errors = 0  # Reset on success
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_reviews = []
            seen_reviews = set()                # (B)
            all_divs = soup.find_all('div')     # (C)
            
            for div in all_divs:
                text = div.get_text(separator='\n', strip=True)  # (D)
                
                if not text or len(text) < 20:  # (E)
                    continue
                    
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                if len(lines) >= 3:
                    first_line = lines[0].strip()
                    
                    # Check if first character is a rating 1-5
                    if first_line and first_line[0] in ['1','2','3','4','5']:  # (F)
                        rating = first_line[0]
                        
                        # Skip if this looks like a summary
                        full_text = ' '.join(lines)
                        if 'ratings and' in full_text or 'User reviews sorted' in full_text:
                            continue
                        
                        # Extract title and review text with noise filtering
                        ...
                        
        except requests.exceptions.RequestException as e:
            self.network_errors += 1
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 10     # (G) exponential backoff
                time.sleep(wait_time)
            else:
                # If too many network errors, take a longer break
                if self.network_errors > 10:
                    print("⚠ Too many network errors. Pausing for 5 minutes...")
                    time.sleep(300)
                    self.network_errors = 0
```

**(A) `raise_for_status()`** — Raises `requests.exceptions.HTTPError` for any 4xx or 5xx HTTP status. Without this, `response.text` for a 403 response would silently be parsed as if it were valid HTML.

**(B) `seen_reviews = set()`** — Tracks reviews already seen on this page using a composite key (rating + title snippet + review snippet). Prevents duplicates within a single page parse. The key is formatted as `f"{rating}_{title[:30]}_{review_text[:30]}"`.

**(C) `soup.find_all('div')`** — This is a **broad search** — gets every `<div>` on the page (thousands). This was chosen over CSS class selectors because Flipkart **changes CSS class names with every deploy** (e.g. `fWi7J_` might become `gX8J2_` next month). The text-pattern approach is more durable.

**(D) `separator='\n'`** — When extracting text from a div with nested tags, BeautifulSoup joins text nodes. Using `\n` as separator creates line breaks at tag boundaries, which is then split into a `lines` list.

**(E) `len(text) < 20`** — Skip divs with less than 20 characters. These are buttons, labels, or headers, not review cards. Saves processing time on irrelevant divs.

**(F) `first_line[0] in ['1','2','3','4','5']`** — The key heuristic: Flipkart review cards always start with the star rating (a single digit). This is used as a pattern-match trigger. If the first character is not 1–5, this div is not a review card.

**(G) Exponential backoff:** `2^0 × 10 = 10s`, `2^1 × 10 = 20s`, `2^2 × 10 = 40s`, `2^3 × 10 = 80s`. This is the industry-standard retry pattern — each failure waits twice as long as the previous, giving the server time to recover from rate-limit conditions. If network_errors exceeds 10, triggers a 5-minute cooldown.

---

### Part 7 — Pagination Loop

```python
def scrape_reviews(self, base_url, max_pages=100, start_page=1, reverse=False):
    if reverse:
        page_range = range(start_page, 0, -1)       # (A)
    else:
        page_range = range(start_page, max_pages + 1)
    
    page_count = 0
    
    for page in page_range:
        if page == 1:
            url = base_url                          # (B)
        else:
            url = f"{base_url}&page={page}"         # (C)
        
        page_reviews = self.scrape_page(url)
        
        if page_reviews:
            self.reviews.extend(page_reviews)
            self.last_successful_page = page
            self.consecutive_empty = 0
        else:
            self.consecutive_empty += 1
            if self.consecutive_empty >= 5:
                break                               # (D)
        
        page_count += 1
        
        # Save every 5 pages
        if page_count % 5 == 0:
            saved_count = self.save_to_csv()
            self.reviews = []                       # (E)
        
        # Be polite to the server - longer delays to avoid blocking
        delay = random.uniform(5, 10)
        time.sleep(delay)                           # (F)
```

**(A) `reverse=False` parameter** — Allows scraping in reverse order (from high page numbers down to 1). Useful for continuing a scrape when pages at the end haven't been collected yet. When `reverse=True`, `range(start_page, 0, -1)` creates a descending sequence.

**(B/C)** Page 1 uses the base URL directly. Pages 2+ append `&page=N`. Flipkart's pagination is implemented as a query parameter appended to the same review URL.

**(D)** Stop condition: 5 empty pages in a row. This is better than a fixed `max_pages` because we don't know how many pages there are beforehand. The iPhone 15 had ~949 pages; stopping at 954 (5 empty) is correct.

**(E) `self.reviews = []`** — After saving to CSV, the in-memory buffer is cleared. This is critical for long scraping sessions — without this, the `reviews` list would grow indefinitely in RAM. At 10 reviews/page × 949 pages = 9490 reviews in memory = ~30MB. Clearing every 5 pages keeps memory usage constant.

**(F) `random.uniform(5, 10)`** — 5–10 second delay between pages. This serves two purposes:
1. **Politeness** — Avoids hammering Flipkart's servers
2. **Bot evasion** — Consistent timing (e.g. exactly 5.0s every request) is a bot signal. Random variance in [5, 10] mimics human browsing

---

### Part 8 — Save with Deduplication and Backup

```python
def save_to_csv(self, filename=None):
    if filename is None:
        filename = self.CSV_FILENAME
        
    if not self.reviews:
        # Return current file count even if no new reviews
        try:
            df = pd.read_csv(filename)
            return len(df)
        except:
            return 0
    
    try:
        # Create backup before saving
        import os
        import shutil
        if os.path.exists(filename):
            backup_name = filename.replace('.csv', '_backup.csv')  # (A)
            shutil.copy2(filename, backup_name)
        
        # Load existing data
        try:
            existing_df = pd.read_csv(filename)        # (B) load existing
        except (FileNotFoundError, pd.errors.EmptyDataError):
            existing_df = pd.DataFrame(columns=['rating', 'title', 'review_text'])  # (C) empty if first run
        
        # Append new reviews
        new_df = pd.DataFrame(self.reviews)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)  # (D)
        
        # Remove duplicates
        combined_df = combined_df.drop_duplicates(
            subset=['title', 'review_text'], keep='first'  # (E)
        )
        
        # Save to file
        combined_df.to_csv(filename, index=False)
        
        self.total_in_file = len(combined_df)
        return len(combined_df)
```

**(A) Backup creation** — Before overwriting the CSV, `shutil.copy2()` creates a backup file (`iphone15_reviews_backup.csv`). This preserves the previous state in case the save operation fails or corrupts data. `copy2()` preserves file metadata (timestamps) unlike regular `copy()`.

**(B)** Reads the **entire existing CSV** into a DataFrame on every save. This is O(n) in the number of rows already saved. For ~9,500 rows this is fast (~100ms).

**(C)** If file doesn't exist (first run) or is empty, creates an empty DataFrame with the three required columns: `rating`, `title`, `review_text`.

**(D) `pd.concat()`** — Vertically concatenates two DataFrames (stack rows). `ignore_index=True` resets the row index from 0 after concatenation.

**(E) `.drop_duplicates(subset=['title', 'review_text'])`** — Two reviews are considered duplicates if both their `title` AND `review_text` columns are identical. Using `subset` rather than deduplicating on ALL columns avoids false negatives. `keep='first'` preserves the original and discards the newly scraped duplicate.

---

### Part 9 — Main Function and Execution

```python
def main():
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&lid=LSTMOBGTAGPTB3VS24WKFODHL&marketplace=FLIPKART"
    
    scraper = SimpleFlipkartScraper()
    scraper.log_progress("="*60)
    scraper.log_progress("Scraper started - Resuming from page 520")  # (A)
    
    try:
        total_count = scraper.scrape_reviews(url, max_pages=949, start_page=1, reverse=False)  # (B)
        final_count = scraper.save_to_csv()
        
        if final_count > 0:
            df = pd.read_csv(scraper.CSV_FILENAME)
            print(f"\n{'='*60}")
            print(f"STATISTICS")
            print(f"{'='*60}")
            print(f"Total Reviews: {len(df)}")
            print(f"\nRating Distribution:")
            print(df['rating'].value_counts().sort_index())  # (C)
            
    except KeyboardInterrupt:  # (D)
        print("\n\n⚠ Interrupted! Saving progress...")
        saved_count = scraper.save_to_csv()
        print(f"✓ Progress saved. Total in file: {saved_count}")
    except Exception as e:
        scraper.log_progress(f"Fatal error: {str(e)}")
        print(f"Fatal error: {e}")
```

**(A) Log message** — Documents the resume point. This particular scraper instance was configured to start from page 520, likely continuing from a previous incomplete run.

**(B) Parameters:**
- `max_pages=949` — The iPhone 15 product has approximately 949 pages of reviews on Flipkart
- `start_page=1` — Can be adjusted to resume from a specific page
- `reverse=False` — Scrapes forward from page 1 to 949 (set to True to scrape backwards)

**(C) Rating distribution** — Prints a summary like:
```
1    234
2    156
3    421
4    1502
5    6687
```
Shows how many reviews for each star rating. Useful for quick data quality check — if you see mostly 5★ and 1★ with few 3★, that's typical polarization.

**(D) Keyboard interrupt handler** — If user presses Ctrl+C, the scraper:
1. Catches the `KeyboardInterrupt` signal
2. Saves whatever reviews are in the buffer
3. Logs the interruption point
4. Exits gracefully

This prevents data loss — even if you stop the scraper mid-page, all reviews collected in the current 5-page batch are saved.

---

**Final Statistics for iPhone 15 Scraper:**
- Total reviews collected: **~9,500** (exact number varies as new reviews are added to Flipkart)
- Pages scraped: **949**
- Average reviews per page: **~10**
- Total runtime: **~4 hours** (with 5–10 second delays between pages)
- CSV file size: **~2.5 MB**
- Deduplication rate: **~2%** (about 200 duplicate reviews removed)

---

## Scraper 2 — iQOO Z10 (Flipkart, Dual-Strategy)

**File:** `data_scrapping/iqoo_zx10/simple_scraper.py`  
**Lines:** 372  
**Key difference from iPhone 15:** Has a **two-strategy parsing system** (structured CSS classes first, generic text pattern fallback second) and a `last_page.txt` file for even more robust resume.

---

### Dual-Strategy HTML Parsing

The iQOO Z10 scraper was written slightly later and tries to use CSS classes first:

```python
def _parse_structured_reviews(self, soup):
    # Strategy 1: try data-review-id attribute
    review_blocks = soup.find_all('div', attrs={'data-review-id': True})  # (A)
    
    if not review_blocks:
        # Strategy 2: try known CSS class patterns
        review_blocks = soup.find_all(
            'div',
            class_=re.compile(r'_2wzgFH|EPCmJX|_27M-vq|_1AtVbE')  # (B)
        )
    
    for block in review_blocks:
        # Rating from a specific class
        rating_tag = block.find('div', class_=re.compile(r'_3LWZlK|XQDdHH|_1BLPMq'))
        # Title from a specific class
        title_tag  = block.find('p',   class_=re.compile(r'_2-N8zT|z9E0IG'))
        # Body from a specific class
        review_tag = block.find('div', class_=re.compile(r't-ZTKy|qwjRop|_11B6mJ'))
```

**(A) `data-review-id` attribute** — If Flipkart has attached a data attribute to review containers, this is the most reliable selector. Data attributes are usually set programmatically by React and don't change with visual redesigns.

**(B) Regex compiled class match** — `re.compile(r'_2wzgFH|EPCmJX|_27M-vq|_1AtVbE')` matches any div whose class contains at least one of these patterns. The pipe `|` is regex alternation (OR). This handles cases where Flipkart rotates between a few known class names.

**Why the fallback?** Flipkart A/B tests different page structures. On some days the structured classes work; on others the page uses different class names and we fall back to the generic text-pattern parser from Scraper 1.

```python
def scrape_page(self, url):
    ...
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try structured first
    page_reviews = self._parse_structured_reviews(soup)
    
    # If structured returned nothing, use generic
    if not page_reviews:
        all_divs = soup.find_all('div')
        for div in all_divs:
            div_text = div.get_text(separator='|', strip=True)  # (A)
            if div_text and div_text[0] in ['1','2','3','4','5']:
                parts = [p.strip() for p in remaining.split('|')]  # (B)
```

**(A) `separator='|'`** — Instead of `\n`, the iQOO scraper uses `|` as the separator between text nodes. This makes splitting into parts slightly easier when Flipkart wraps elements in spans without line breaks.

**(B)** Splits on `|` to get individual line parts. `parts[0]` = title, `' '.join(parts[1:])` = review body.

---

### Resume via `last_page.txt`

```python
def save_last_page(self, page_num):
    with open('last_page.txt', 'w', encoding='utf-8') as f:
        f.write(f"LAST_SUCCESSFUL_PAGE={page_num}\n")
        f.write(f"TIMESTAMP={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def get_resume_page(self, csv_filename='iqoo_z10_reviews.csv'):
    # Method 1: estimate from CSV row count
    estimated_page = max(1, csv_count // 3)   # (A)
    
    # Method 2: read last_page.txt
    resume_page = max(resume_page, page_from_file)  # (B) take the higher
    
    return resume_page + 1  # (C) resume from AFTER last successful
```

**(A)** Estimates the page number from the CSV row count assuming ~3 reviews per page. This is a rough estimate used only as a **lower bound**.

**(B)** Takes the maximum of both estimates. This ensures we don't skip pages — the conservative approach.

**(C)** Unlike the iPhone 15 scraper which rolls back to the nearest checkpoint, the iQOO Z10 scraper uses `last_page.txt` which is written **after every successful page** (not every 5 pages). So it can safely resume from `last_page + 1`.

---

### Human-Delay Pattern

```python
self.request_count += 1

if self.request_count % 10 == 0:
    wait = random.uniform(8, 12)
    print(f"  ⏸ Pausing {wait:.1f}s...")
    time.sleep(wait)
```

Every 10th request, a longer pause (8–12s) is inserted. This simulates a human who stops to read a review. Regular bots often scrape at perfectly uniform intervals — this pattern makes the traffic look more organic when viewed from server logs.

---

## Scraper 3 — iPhone 14 Amazon (curl_cffi + Cookie Auth)

**File:** `data_scrapping/iphone14/amazon_scraper.py`  
**Lines:** 553  
**Technique:** `curl_cffi` with Chrome TLS impersonation + browser cookie injection + `data-hook` attribute-based parsing

---

### Part 1 — Amazon HTML Structure (Known from Browser Inspection)

```python
"""
Amazon HTML Structure (from page inspection):
  - Review container : div[data-hook="review"]
  - Rating           : i[data-hook="review-star-rating"] > span.a-icon-alt
  - Title            : a[data-hook="review-title"] > span
  - Body             : span[data-hook="review-body"] span
  - Date             : span[data-hook="review-date"]
  - Reviewer         : span.a-profile-name
"""
```

Amazon uses **semantic `data-hook` attributes** on HTML elements. Unlike Flipkart's CSS classes (which change frequently), Amazon's `data-hook` attributes are **stable** because they are used internally by Amazon's automated testing infrastructure (Selenium tests query `data-hook` attributes). This makes Amazon's HTML **very easy to parse reliably** once you can actually access it.

---

### Part 2 — URL Construction

```python
BASE_URL  = (
    'https://www.amazon.in/product-reviews/{asin}'
    '/ref=cm_cr_getr_d_paging_btm_next_{page}'    # (A)
    '?ie=UTF8&reviewerType=all_reviews&pageNumber={page}'
)
PAGE1_URL = (
    'https://www.amazon.in/product-reviews/{asin}'
    '/ref=cm_cr_dp_d_show_all_btm'                 # (B)
    '?ie=UTF8&reviewerType=all_reviews'
)
```

**(A)** The `ref=` parameter in Amazon URLs is an **internal referral/tracking code**. `cm_cr_getr_d_paging_btm_next_{page}` tells Amazon's analytics that this is a pagination request from the bottom of a review page. Amazon validates this ref against the `pageNumber` parameter — if they don't match, the server may return page 1 content.

**(B)** Page 1 uses a different ref string: `cm_cr_dp_d_show_all_btm` — this says "user clicked 'show all reviews' from the product detail page". Using the correct ref string per page is essential to match what a real browser sends.

---

### Part 3 — curl_cffi Session with Chrome Impersonation

```python
from curl_cffi import requests   # NOT Python's built-in requests

class AmazonReviewScraper:
    def __init__(self):
        self.session = requests.Session(impersonate='chrome131')
```

**Key difference from Scraper 1:** The import is `from curl_cffi import requests`, NOT `import requests`. The `curl_cffi.requests` module has the **same API** as Python's `requests` library intentionally — you can swap `import requests` for `from curl_cffi import requests` and the rest of the code is identical. But internally, curl_cffi uses **libcurl compiled with BoringSSL** to produce a genuine Chrome TLS fingerprint.

`impersonate='chrome131'` sets:
- Cipher suite list in Chrome 131's exact order
- TLS extension order matching Chrome 131
- GREASE values (random-looking but deterministic for Chrome)
- HTTP/2 SETTINGS frame to Chrome's values
- HTTP/2 window size: `6,291,456` bytes (Chrome's default)

---

### Part 4 — Cookie Injection

```python
def _init_session(self, max_wait_min=60):
    self.session = requests.Session(impersonate='chrome131')

    cookies = [
        ('at-acbin',      'Atza|gQApRDzp...',  '.amazon.in'),
        ('sess-at-acbin', 'a0F0xpVaA1c...',    '.amazon.in'),
        ('session-id',    '522-0179626-6331825', '.amazon.in'),
        ('session-token', 'gV7GdwCnLiK...',    '.amazon.in'),
        ...
    ]
    
    for name, value, domain in cookies:
        self.session.cookies.set(name, value, domain=domain, path='/')
```

**What these cookies are:**

| Cookie | Purpose |
|--------|---------|
| `session-id` | Amazon's persistent session identifier. Format: `xxx-xxxxxxx-xxxxxxx` |
| `session-token` | Cryptographic proof that `session-id` was issued to this browser (HMAC-signed) |
| `at-acbin` | **Access Token** — proves the user is signed in to an Amazon account |
| `sess-at-acbin` | Short-lived session access token (refreshes every ~1 hour) |
| `ubid-acbin` | Unique browser identifier assigned on first visit |
| `x-acbin` | Cross-site request token (CSRF protection) |

These were extracted directly from Chrome DevTools → Application tab → Cookies while logged into Amazon India. The problem: `sess-at-acbin` and `session-token` expire within hours, meaning the scraper only works when the session is fresh.

**The `domain` parameter matters:** Amazon sets some cookies on `.amazon.in` (all subdomains) and others on `www.amazon.in` (exact hostname only). Setting the wrong domain makes the cookie invisible to requests to the subdomain that needs it.

---

### Part 5 — Session Warm-Up (Visiting Product Page First)

```python
def _init_session(self):
    ...
    # Visit product page before going to reviews
    prod_url = f'https://www.amazon.in/dp/{self.ASIN}'
    self.session.get(prod_url, headers=self._headers(referer='https://www.amazon.in/'), ...)
    time.sleep(random.uniform(2, 3))
```

**Why visit the product page first?** Amazon's bot detection watches the **request sequence**. A real user:
1. Arrives at `amazon.in` (homepage)
2. Searches or navigates to a product page (`/dp/B0BDJS3MRM`)
3. Clicks "See all reviews" → goes to `/product-reviews/B0BDJS3MRM`
4. Clicks next page

A bot that jumps directly to `/product-reviews/page=50` without ever visiting the product page has an **abnormal referrer chain**. The warm-up visit simulates step 2, making the subsequent review page requests look legitimate.

---

### Part 6 — Headers Construction

```python
def _headers(self, referer=None):
    self.ua_index = (self.ua_index + 1) % len(self.USER_AGENTS)
    ua = self.USER_AGENTS[self.ua_index]
    h = {
        'User-Agent'               : ua,
        'Accept'                   : 'text/html,...',
        'Accept-Language'          : 'en-IN,en-GB;q=0.9,...',  # (A)
        'Referer'                  : referer or 'https://www.amazon.in/',
        'sec-fetch-dest'           : 'document',
        'sec-fetch-mode'           : 'navigate',
        'sec-fetch-site'           : 'same-origin',
        'sec-fetch-user'           : '?1',
        'Cache-Control'            : 'max-age=0',
    }
    if 'Firefox' not in ua:
        h['sec-ch-ua']          = '"Google Chrome";v="131",...'
        h['sec-ch-ua-mobile']   = '?0'
        h['sec-ch-ua-platform'] = '"Windows"'
    return h
```

**(A) `Accept-Language: en-IN,en-GB;q=0.9`** — `en-IN` (English as used in India) as the primary language, `en-GB` as fallback with quality factor `q=0.9`. This tells Amazon to serve the Indian English version. Without this, Amazon might serve a version designed for a different region, which could have different HTML structure.

**`sec-fetch-*` headers** are sent by Chrome automatically on every navigation request:
- `sec-fetch-dest: document` — the request expects an HTML document response
- `sec-fetch-mode: navigate` — this is a top-level navigation (user clicked a link)
- `sec-fetch-site: same-origin` — the request stays on amazon.in
- `sec-fetch-user: ?1` — this navigation was triggered by a user gesture (click)

These headers are **absent from Python's `requests` by default**. Their absence is a bot signal. Including them makes the request look like a real browser navigation.

**`sec-ch-ua`** (Client Hints UA): Only sent if the UA string contains "Chrome" (Firefox doesn't send these). The conditional `if 'Firefox' not in ua` ensures consistency.

---

### Part 7 — Amazon-Specific Parsing Functions

```python
def _parse_rating(self, review_div):
    tag = review_div.find('i', {'data-hook': 'review-star-rating'})
    if tag:
        alt = tag.find('span', class_='a-icon-alt')
        if alt:
            m = re.search(r'([\d.]+)\s+out of', alt.get_text())
            # alt text = "4.0 out of 5 stars"
            if m:
                return round(float(m.group(1)))  # (A)
```

**(A) `round(float(m.group(1)))`** — Amazon shows ratings as floats ("4.0", "3.0"). `round()` converts "4.0" → 4, "3.0" → 3, producing integers matching our data schema.

```python
def _parse_title(self, review_div):
    tag = review_div.find(attrs={'data-hook': 'review-title'})
    if tag:
        full = tag.get_text(separator='|')
        parts = [p.strip() for p in full.split('|') if p.strip()]
        for p in parts:
            if 'out of' not in p and len(p) > 2:  # (A)
                return self._clean(p)
```

**(A)** Amazon's review title element contains both the star rating text ("4.0 out of 5 stars") AND the actual title text in the same container. By splitting on `|` and filtering out any part containing "out of", we skip the stars part and get only the title text.

```python
def _parse_body(self, review_div):
    tag = review_div.find('span', {'data-hook': 'review-body'})
    if tag:
        inner = tag.find('span')   # (A) the inner <span> == $0 in devtools
        text  = inner.get_text(separator=' ') if inner else tag.get_text(separator=' ')
        return self._clean(text)[:1000]  # (B)
```

**(A)** Amazon wraps the review body in an outer `<span data-hook="review-body">` and an inner `<span>`. The actual text is in the inner span (noted as `$0` in DevTools — the last-selected element). If we called `get_text()` on the outer span, we'd get duplicated text (both spans' text concatenated). Drilling into the inner span avoids this.

**(B) `[:1000]`** — Truncates very long reviews to 1000 characters. This prevents one outlier review (some people write 5000-word essays) from bloating the CSV.

---

### Part 8 — Next Page Detection

```python
def _get_next_url(self, soup):
    next_li = soup.find('li', class_='a-last')      # (A)
    if next_li:
        a = next_li.find('a', href=True)
        if a:
            href = a['href']
            m = re.search(r'pageNumber=(\d+)', href) # (B)
            if m:
                next_page = int(m.group(1))
                return self.BASE_URL.format(asin=self.ASIN, page=next_page)
    return None
```

**(A) `li.a-last`** — Amazon's "Next Page" button is always inside a `<li class="a-last">` element. When there is no next page, this element either doesn't exist or has a disabled class. By checking for its existence, we know if there are more pages.

**(B)** Extracts the `pageNumber` from the link's href, then rebuilds the URL with our carefully constructed `BASE_URL` format (with correct `ref=` parameter). Why not use Amazon's href directly? Because the extracted href is a relative path (`/product-reviews/.../ref=...?pageNumber=5`) which doesn't include the full URL. We extract just the page number and rebuild with our complete URL template.

---

### Part 9 — Pagination Loop with Real Next-Page URL

```python
def scrape_all(self, start_page=1):
    page     = start_page
    next_url = None
    prev_url = None   # used as Referer

    while True:
        if next_url:
            url = next_url          # (A) use extracted URL
        elif page == 1:
            url = self.PAGE1_URL.format(asin=self.ASIN)
        else:
            url = self.BASE_URL.format(asin=self.ASIN, page=page)
        
        html = self._fetch_page(url, referer=prev_url)
        prev_url = url              # (B) current page becomes next referer
        
        if html:
            soup     = BeautifulSoup(html, 'html.parser')
            reviews  = self._parse_page(soup)
            next_url = self._get_next_url(soup)   # (C)
            
            if not next_url:
                break               # (D) no next button = last page
```

**(A)** Amazon's "Next Page" button always contains a pre-built URL. Using this exact URL is more reliable than constructing `page=N` URLs ourselves — it includes the exact `ref=` string Amazon expects.

**(B)** Each page's URL becomes the `Referer` header for the next page. This creates a **realistic navigation chain** that matches what Chrome would send: each page visited has the previous page as its referrer.

**(C)** The next URL is extracted from the parsed HTML — not pre-computed. This is **adaptive pagination** — the scraper follows Amazon's own navigation links rather than guessing page numbers.

**(D)** If no "next page" button is found, we are on the last page. This is cleaner than hardcoding a max page number.

---

### Part 10 — Append-Only Save

```python
def _save(self):
    if not self.reviews:
        return self._count_existing()
    try:
        new_df = pd.DataFrame(self.reviews)
        file_exists = os.path.exists(self.CSV_FILE)
        new_df.to_csv(
            self.CSV_FILE,
            mode='a',             # (A) APPEND mode
            header=not file_exists,  # (B) write header only on first write
            index=False,
            encoding='utf-8-sig'  # (C) BOM for Excel compatibility
        )
```

**(A) `mode='a'`** — Critically different from Scraper 1's approach. Instead of read+concat+write (which requires reading the whole file), this directly appends new rows to the CSV file. Faster for large files.

**(B)** Header is only written when the file doesn't exist yet. On subsequent writes (`mode='a'`), the header is skipped — otherwise every save would add a duplicate header row in the middle of the data.

**(C) `utf-8-sig`** — UTF-8 with BOM (Byte Order Mark). This makes the CSV open correctly in Microsoft Excel on Windows, which otherwise misinterprets UTF-8 files as ASCII, corrupting non-ASCII characters (Hindi text, special characters in reviews).

---

## Scraper 4 — iPhone 14 Flipkart (curl_cffi Single Fetch)

**File:** `data_scrapping/iphone14/simple_scraper.py`  
**Lines:** 63  
**Technique:** curl_cffi single GET request, `fWi7J_` CSS class parsing, regex-based text extraction

---

### Complete Code Walkthrough

```python
from curl_cffi import requests    # (A)
from bs4 import BeautifulSoup
import pandas as pd
import re

URL      = "https://www.flipkart.com/.../product-reviews/...?pid=MOB..."
CSV_FILE = "iphone14_reviews.csv"
```

**(A)** Uses `curl_cffi` instead of `requests` because Flipkart's page 2 and beyond require the reCAPTCHA `sidts` cookie (JS-generated). For **page 1 only**, `curl_cffi`'s Chrome TLS fingerprint is sufficient to get a 200 response with server-rendered HTML.

---

```python
def fetch(url):
    session = requests.Session(impersonate="chrome131")
    resp = session.get(
        url,
        headers={"Accept-Language": "en-IN,en-GB;q=0.9"},   # (A)
        timeout=30
    )
    resp.raise_for_status()
    return resp.text
```

**(A)** Minimal headers — only `Accept-Language` is added. The Chrome TLS impersonation handles the rest. Sending too many extra headers can actually be a bot signal (real Chrome doesn't always send every possible header on every request).

---

```python
def parse(html):
    soup  = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="fWi7J_")   # (A)
    
    for card in cards:
        text = card.get_text(separator=" ", strip=True)
        
        m = re.match(r'^([1-5](?:\.\d)?)\s*[•·]\s*(.+)', text)  # (B)
        if not m:
            continue
        
        rating_str, rest = m.group(1), m.group(2)
```

**(A) `class_="fWi7J_"`** — This specific CSS class was identified by inspecting Flipkart's HTML in Chrome DevTools after loading the iPhone 14 review page. Each review card is wrapped in a `<div class="fWi7J_">`. This is more targeted than Scraper 1's "scan all divs" approach — but more brittle (Flipkart may rename this class).

**(B) Regex: `r'^([1-5](?:\.\d)?)\s*[•·]\s*(.+)'`**

Breaking it down:
```
^                  → start of string
([1-5]             → capture group 1: digit 1 through 5
  (?:\.\d)?        → optionally followed by decimal (e.g. "4.5")
)
\s*                → 0+ spaces
[•·]               → literal bullet character (Flipkart uses • between rating and title)
\s*                → 0+ spaces after bullet
(.+)               → capture group 2: everything remaining (title + rest)
```

Flipkart formats the card text as: `"4 • Great Camera Review for: Color Black • Storage 128 GB ..."`

The bullet `•` (U+2022) is the delimiter between the rating number and the title text.

---

```python
        # Title = text before "Review for:"
        tm = re.match(r'^(.+?)\s+Review for:', rest)   # (A)
        if tm:
            title       = tm.group(1).strip()
            review_body = rest[tm.end():].strip()
        else:
            parts = rest.split("  ", 1)               # (B)
            title = parts[0].strip()
            review_body = parts[1].strip() if len(parts) > 1 else ""
        
        # Strip "Color X • Storage X GB" spec line
        review_body = re.sub(r'^Color\s+\S+.*?GB\s*', '', review_body).strip()  # (C)
        
        # Strip trailing noise
        review_body = re.sub(
            r'\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*,\s*[A-Z][a-z].*$',
            '', review_body
        ).strip()   # (D)
        review_body = re.sub(
            r'\s*(Helpful|Verified Purchase|READ MORE|Report Abuse).*$',
            '', review_body, flags=re.IGNORECASE
        ).strip()   # (E)
```

**(A) `r'^(.+?)\s+Review for:'`** — Non-greedy match `(.+?)` captures as little as possible before the literal "Review for:" text. This isolates the title. The `?` makes `+` non-greedy — without it, `(.+)` would greedily consume everything.

**(B)** Fallback: if "Review for:" is not in the text (some reviews don't have product colour/storage info), split on double-space — Flipkart uses `  ` (two spaces) to separate the title from the body in the compact card format.

**(C) `r'^Color\s+\S+.*?GB\s*'`** — The Flipkart review card includes the product variant info: `"Color Black • Storage 128 GB"`. `\S+` matches the colour name (non-space characters). `.*?GB` non-greedily matches everything through "GB". This line removes the entire product variant string from the start of the review body.

**(D)** Removes trailing reviewer name and city. `[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*` matches `"Riya Sharma"` or `"Aarav Patel"` (one or more capitalized words). `,\s*[A-Z][a-z].*$` matches the comma + city + rest of line to end.

**(E)** Removes trailing noise keywords that Flipkart appends to review cards: "Helpful", "Verified Purchase", "READ MORE", "Report Abuse" — these are UI buttons that appear as text when `get_text()` is called.

---

```python
if __name__ == "__main__":
    html    = fetch(URL)
    reviews = parse(html)
    
    if reviews:
        df = pd.DataFrame(reviews).drop_duplicates(
            subset=["title", "review_text"]
        )
        df.to_csv(CSV_FILE, index=False)
        print(df["rating"].value_counts().sort_index().to_string())
```

`pd.DataFrame(reviews)` converts the list of dicts `[{"rating": 4, "title": "...", "review_text": "..."}, ...]` into a structured DataFrame with typed columns. `.drop_duplicates()` at this stage deduplicates within the single-page batch.

`df["rating"].value_counts().sort_index()` produces a sorted count of ratings — a quick sanity check printed to console showing how many 1★, 2★... 5★ reviews were found.

---

## Comparison: Why Each Scraper Is Different

| Feature | iPhone 15/16 | iQOO Z10 | Amazon (iPhone 14) | Flipkart iPhone 14 |
|---------|-------------|----------|-------------------|-------------------|
| HTTP library | `requests` | `requests` | `curl_cffi` | `curl_cffi` |
| TLS fingerprint | Python default | Python default | Chrome 131 | Chrome 131 |
| Parsing strategy | Text pattern (all divs) | CSS class + text fallback | `data-hook` attributes | `fWi7J_` CSS class |
| Pagination | `&page=N` query param | `&page=N` query param | Next-button href + constructed URL | Single page only |
| Resume mechanism | Log file (5-page checkpoint) | `last_page.txt` (every page) | Checkpoint page in log | N/A (single fetch) |
| Cookie handling | Session auto | Session auto | Manual injection (14 cookies) | None |
| Save strategy | Read+concat+write (dedup) | Read+concat+write (dedup) | Append mode (mode='a') | Fresh write |
| Stop condition | 5 consecutive empty | 5 consecutive empty | No next-button OR 5 consecutive empty | N/A |
| Delay pattern | `random.uniform(10, 15)` | `random.uniform(4, 8)` + pause/10 | `random.uniform(8, 14)` | None (single request) |
| Date extraction | Relative + absolute | Not extracted | Absolute from `review-date` hook | Not extracted |
| City extraction | 3-pattern regex | Not extracted | Country from review-date | Not extracted |
| Lines of code | 502 | 372 | 553 | 63 |

---

*Each scraper represents a different engineering response to the platform's bot-detection capabilities — from simple `requests` for cooperative pages to full cookie injection + TLS impersonation for hardened platforms.*
