"""Amazon India Review Scraper - iPhone 14 (ASIN: B0BDJS3MRM)
HTML Structure (from page inspection):
  - Review container : div[data-hook="review"]
  - Rating           : i[data-hook="review-star-rating"] > span.a-icon-alt  (e.g. "4.0 out of 5 stars")
  - Title            : a[data-hook="review-title"] > span  (last span, skip star span)
  - Body             : span[data-hook="review-body"] span  (inner span == $0 in devtools)
  - Date             : span[data-hook="review-date"]       (e.g. "Reviewed in India on 17 December 2023")
  - Reviewer         : span.a-profile-name
  - Verified         : span[data-hook="avp-badge"]
Pagination URL:
  https://www.amazon.in/product-reviews/B0BDJS3MRM/ref=cm_cr_getr_d_paging_btm_next_{page}
  ?ie=UTF8&reviewerType=all_reviews&pageNumber={page}
"""

import os
from curl_cffi import requests   # impersonates Chrome TLS fingerprint
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime


class AmazonReviewScraper:
    ASIN        = 'B0BDJS3MRM'
    CSV_FILE    = 'iphone14_amazon_reviews.csv'
    LOG_FILE    = 'amazon_save.txt'
    # Exact ref format Amazon uses for pagination — confirmed from browser
    # Only change: all_reviews instead of avp_only_reviews, no filterByStar
    BASE_URL    = (
        'https://www.amazon.in/product-reviews/{asin}'
        '/ref=cm_cr_getr_d_paging_btm_next_{page}'
        '?ie=UTF8&reviewerType=all_reviews&pageNumber={page}'
    )
    PAGE1_URL   = (
        'https://www.amazon.in/product-reviews/{asin}'
        '/ref=cm_cr_dp_d_show_all_btm'
        '?ie=UTF8&reviewerType=all_reviews'
    )

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
    ]

    def __init__(self):
        self.session        = requests.Session(impersonate='chrome131')  # Chrome TLS fingerprint
        self.ua_index       = 0
        self.reviews        = []          # in-memory buffer
        self.seen_keys      = set()       # global dedup across ALL pages
        self.total_in_file  = self._count_existing()
        self.last_page      = 0
        self.consecutive_empty = 0

    # ------------------------------------------------------------------ helpers
    def _count_existing(self):
        try:
            return len(pd.read_csv(self.CSV_FILE))
        except Exception:
            return 0

    def _get_last_page_from_log(self):
        """Parse log file to find last successfully scraped page."""
        try:
            with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in reversed(lines):
                m = re.search(r'Page (\d+):.*Found', line)
                if m:
                    return int(m.group(1))
        except Exception:
            pass
        return 0

    def _get_last_checkpoint_page(self):
        """Find the last page that was actually SAVED (checkpointed) from the log.
        Looks for lines like: Checkpoint: Saved at page N
        Returns 0 if no checkpoint found (start fresh).
        """
        try:
            with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in reversed(lines):
                m = re.search(r'Checkpoint: Saved at page (\d+)', line)
                if m:
                    return int(m.group(1))
        except Exception:
            pass
        return 0

    def _load_seen_keys(self):
        """Pre-load review keys from existing CSV so we never re-save duplicates on resume."""
        try:
            df = pd.read_csv(self.CSV_FILE)
            for _, row in df.iterrows():
                key = f"{row['rating']}_{str(row['title'])[:30]}_{str(row['review_text'])[:30]}"
                self.seen_keys.add(key)
            print(f"✓ Loaded {len(self.seen_keys)} existing review keys for dedup")
        except Exception:
            pass

    def _get_next_url(self, soup):
        """Extract pageNumber from Amazon's <li class='a-last'><a href='...'>
        then build the exact correct URL with all_reviews and no star filter.
        """
        next_li = soup.find('li', class_='a-last')
        if next_li:
            a = next_li.find('a', href=True)
            if a:
                href = a['href']
                m = re.search(r'pageNumber=(\d+)', href)
                if m:
                    next_page = int(m.group(1))
                    return self.BASE_URL.format(asin=self.ASIN, page=next_page)
        return None

    def log(self, msg):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")

    def _headers(self, referer=None):
        self.ua_index = (self.ua_index + 1) % len(self.USER_AGENTS)
        ua = self.USER_AGENTS[self.ua_index]
        h = {
            'User-Agent'              : ua,
            'Accept'                  : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language'         : 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding'         : 'gzip, deflate, br',
            'Connection'              : 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer'                 : referer or 'https://www.amazon.in/',
            'sec-fetch-dest'          : 'document',
            'sec-fetch-mode'          : 'navigate',
            'sec-fetch-site'          : 'same-origin',
            'sec-fetch-user'          : '?1',
            'Cache-Control'           : 'max-age=0',
        }
        if 'Firefox' not in ua:
            h['sec-ch-ua']          = '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
            h['sec-ch-ua-mobile']   = '?0'
            h['sec-ch-ua-platform'] = '"Windows"'
        return h

    def _init_session(self, max_wait_min=60):
        """Inject hardcoded Amazon.in cookies from the signed-in browser session."""
        self.session = requests.Session(impersonate='chrome131')

        # (name, value, domain) — exact domains from browser DevTools
        cookies = [
            ('at-acbin',        'Atza|gQApRDzpAwEBAKHKpOfx9sj8OBhb-iGgDgwqn-HezwX5qN_HGbZkE7XskDXF9BIVNHRZXCAuAdWBFN-ZgTSQJZCco9TstqxlNaI6lRFxEc_X2fsV9AucK9vvUkQso9ka-35FCue_CXdPqlYBT-BQUWe08XMYmC-nB1EFJ79wTQuXTGUz7aFfTZ-ksFcSwZ910VG53_L10_xgpJk4oqxSIq8Muw9ZbKMeaIxHT8C6b7pJuc0DTHMb5ZbH8ojpEuFXjE4YhhsV-efe70DQlvJAsZK0b5IrkNdyJ25VocmENVgbiELDMuxOg63rmuppI6rz8s_vornM6tqWC90Cn4N1CRxnHlw6s5yHvdLKAGAquA',
             '.amazon.in'),
            ('sess-at-acbin',   'a0F0xpVaA1cAAlV4S1+7WTET2lgodTlsB6+3jQEFmgs=',
             '.amazon.in'),
            ('session-id',      '522-0179626-6331825',
             '.amazon.in'),
            ('session-id-time', '2082787201l',
             '.amazon.in'),
            ('session-token',   'gV7GdwCnLiKpf3zlr8DejVFf6D1qo8vGTa9kcOBpMPQ6ZnLy+g4MxRb0p2k25EI8on7WJ0wBXl8VnHFcCjojyBc/NG2RqQg/lKiAg15TfJQC7rATVL8xqh/2ll8rZqw0g7CmprEH25gRJ8tWWxInbbXXUEdz+ewZNfscNtK+GOjWuCwaklV1bKGAXFjqrbmglWSeLKnTQBPn7MS7FRyTmFpmnSMONzafaU+2ZvmU/gsjyiC/ejrGdaiP9s82eE6XLsUyI3Iog8qxMhpGzTMQ/YamdfiJVqvT2fE/GcZGlBjREZUR2vbz8vPbLZMIRm2KgHbPRLRWNI4j3MupQlVypYkg6KnIg+d+j82oWqOUuwrWmmoTN9z/jM+J9dhpvK9v',
             '.amazon.in'),
            ('ubid-acbin',      '521-5890498-6216253',
             '.amazon.in'),
            ('x-acbin',         '"Plsud9HAH3@vsAlSKBai7ZsFRtT?xQFgqNJ5ZWapin5vWSCksTVCW3H3NQxMjxka"',
             '.amazon.in'),
            ('sso-state-acbin', 'Xdsso|ZQG8qmxLHoaDJ3zEa95jYQRS7SK8gp0gyoGikL6Lq3FfrzEtY1uKxkCdIEYyBTrDhVpatfCOQ8bEpyOxsHREoQuSZH4iU4qVJxhRP1JOhExXlhQL',
             '.amazon.in'),
            ('sst-acbin',       'Sst1|PQJ6Lnb9-fnCe8T0q34MRBQVCiELUbqMuu_T8PjXqEZUUq7-4LqyAFlWyf8k_O1DoGzWP491BNzS7CoCVb0Y7gapQ59TveJABmE170FPiXSTv18m0DDK09gpw4HojdfsK83iJA8ajnS2vqCUoe7senetXw53fHNVqm0fWsTntZo6iWyAtPRFBO-PbIu9nGwZ2nJf9aTaAwV9V2YwTLnFrXKx81J_RU2YGhJHT5h6q-ST5OBH92r-HTwlNN2OvNmWfr43fGQaUXtUO82nEpgPnX9D2Xo5X7zcTjzV2FTsHBNQhUfHqau1ykCsDET5WabV8hGG',
             '.amazon.in'),
            ('lc-acbin',        'en_IN',
             '.amazon.in'),
            ('i18n-prefs',      'INR',
             '.amazon.in'),
            ('csm-hit',         'tb:W26MJD0TJX46P9XT6SH4+sa-HBD0SMT54ZBPMJXJ16Z0-C3HPA5FB6FTAVHS193F3|1771421296506&t:1771421296506&adb:adblk_no',
             'www.amazon.in'),
            ('rx',              'AQALK5GangHiXM0DTQPONkzAwag=@AWK6lWk=',
             '.www.amazon.in'),
            ('rxc',             'AOBj9Nqo//IWY7V9GvQ',
             'www.amazon.in'),
        ]

        for name, value, domain in cookies:
            self.session.cookies.set(name, value, domain=domain, path='/')

        print(f"✓ Injected {len(cookies)} Amazon.in cookies")

        # Verify authentication
        try:
            r = self.session.get(
                'https://www.amazon.in/product-reviews/' + self.ASIN,
                headers=self._headers(),
                timeout=30,
                allow_redirects=True,
                impersonate='chrome131'
            )
            if 'ap/signin' in r.url:
                print("❌ Still redirecting to sign-in — cookies may be expired.")
            else:
                print(f"✓ Authenticated! (status {r.status_code})")
        except Exception as e:
            print(f"⚠ Check failed: {e}")

        time.sleep(random.uniform(2, 4))

        # Visit the product page first (like a real user would before reading reviews)
        try:
            prod_url = f'https://www.amazon.in/dp/{self.ASIN}'
            self.session.get(prod_url, headers=self._headers(referer='https://www.amazon.in/'), timeout=20, impersonate='chrome131')
            print(f"✓ Visited product page")
            time.sleep(random.uniform(2, 3))
        except Exception:
            pass

    # ------------------------------------------------------------------ parsing
    def _clean(self, text):
        if not text:
            return ''
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)    # remove non-ASCII / emojis
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _parse_rating(self, review_div):
        """Extract numeric rating from star text like '4.0 out of 5 stars'."""
        tag = review_div.find('i', {'data-hook': 'review-star-rating'})
        if not tag:
            tag = review_div.find('span', {'data-hook': 'review-star-rating'})
        if tag:
            alt = tag.find('span', class_='a-icon-alt')
            if alt:
                m = re.search(r'([\d.]+)\s+out of', alt.get_text())
                if m:
                    return round(float(m.group(1)))
        return None

    def _parse_title(self, review_div):
        tag = review_div.find(attrs={'data-hook': 'review-title'})
        if tag:
            # Remove the star-rating span text, keep only the actual title text
            full = tag.get_text(separator='|')
            parts = [p.strip() for p in full.split('|') if p.strip()]
            for p in parts:
                if 'out of' not in p and len(p) > 2:
                    return self._clean(p)
        return ''

    def _parse_body(self, review_div):
        tag = review_div.find('span', {'data-hook': 'review-body'})
        if tag:
            inner = tag.find('span')   # the inner <span> == $0 in devtools
            text  = inner.get_text(separator=' ') if inner else tag.get_text(separator=' ')
            return self._clean(text)[:1000]
        return ''

    def _parse_date(self, review_div):
        """Extract formatted date from 'Reviewed in India on 28 January 2026'"""
        tag = review_div.find('span', {'data-hook': 'review-date'})
        if tag:
            text = tag.get_text(strip=True)
            # Format: "Reviewed in India on 28 January 2026"
            m = re.search(r'on\s+(\d+\s+\w+\s+\d{4})', text)
            if m:
                try:
                    dt = datetime.strptime(m.group(1), '%d %B %Y')
                    return dt.strftime('%b %Y')
                except Exception:
                    pass
        return 'N/A'

    def _parse_location(self, review_div):
        """Extract country from 'Reviewed in India on ...' — Amazon doesn't expose city."""
        tag = review_div.find('span', {'data-hook': 'review-date'})
        if tag:
            text = tag.get_text(strip=True)
            # "Reviewed in India on 28 January 2026"
            m = re.search(r'Reviewed in ([A-Za-z ]+?) on', text)
            if m:
                return m.group(1).strip()
        return 'N/A'

    def _parse_reviewer(self, review_div):
        """Extract reviewer name from genome-widget."""
        tag = review_div.find(attrs={'data-hook': 'genome-widget'})
        if tag:
            name_tag = tag.find('span', class_='a-profile-name')
            if name_tag:
                return self._clean(name_tag.get_text())
            # Fallback: first plain text node
            text = tag.get_text(strip=True)
            if text and len(text) < 60:
                return self._clean(text)
        return 'N/A'

    def _parse_page(self, soup):
        """Return list of review dicts from a parsed page.
        Amazon uses <li data-hook="review"> containers (not <div>).
        """
        containers = soup.find_all(attrs={'data-hook': 'review'})  # catches <li> or <div>
        results    = []
        seen       = set()

        for item in containers:
            rating   = self._parse_rating(item)
            title    = self._parse_title(item)
            body     = self._parse_body(item)
            date     = self._parse_date(item)
            location = self._parse_location(item)
            reviewer = self._parse_reviewer(item)

            if not rating or not body or len(body) < 10:
                continue
            if not title or len(title) < 2:
                title = 'No title'

            key = f"{rating}_{title[:30]}_{body[:30]}"
            if key in seen or key in self.seen_keys:
                continue
            seen.add(key)
            self.seen_keys.add(key)

            results.append({
                'rating'     : rating,
                'title'      : title,
                'review_text': body,
                'date'       : date,
                'location'   : location,
                'reviewer'   : reviewer,
            })

        return results

    # ------------------------------------------------------------------ scrape
    def _fetch_page(self, url, retries=4, referer=None):
        for attempt in range(retries):
            try:
                r = self.session.get(
                    url,
                    headers=self._headers(
                        referer=referer or 'https://www.amazon.in/product-reviews/' + self.ASIN
                    ),
                    timeout=30,
                    impersonate='chrome131'
                )
                if r.status_code == 200:
                    if 'ap/signin' in r.url:
                        self.log(f"Sign-in redirect on attempt {attempt+1}")
                        print(f"⚠ Sign-in detected — cookies expired. Retrying in 20s...")
                        time.sleep(20)
                        continue
                    return r.text
                elif r.status_code == 503:
                    wait = 30 * (attempt + 1)
                    self.log(f"503 on attempt {attempt+1}, waiting {wait}s")
                    print(f"⚠ 503 — waiting {wait}s...")
                    time.sleep(wait)
                elif r.status_code == 403:
                    wait = 60 * (attempt + 1)
                    self.log(f"403 on attempt {attempt+1}, waiting {wait}s")
                    print(f"⚠ 403 — waiting {wait}s...")
                    time.sleep(wait)
                    self._init_session(max_wait_min=30)
                else:
                    self.log(f"HTTP {r.status_code} on attempt {attempt+1}")
                    time.sleep(15)
            except Exception as e:
                wait = 15 * (attempt + 1)
                self.log(f"Error on attempt {attempt+1}: {str(e)[:80]}")
                print(f"⚠ Error: {str(e)[:60]} — retrying in {wait}s...")
                time.sleep(wait)
        return None

    def scrape_all(self, start_page=1):
        print(f"\nStarting from page {start_page}...\n")
        page     = start_page
        next_url = None   # Will be populated from each page's HTML
        prev_url = None   # Used as Referer for the next request

        while True:
            # Always prefer the REAL next-page link extracted from HTML.
            # Fall back to constructed URL only for the very first fetch.
            if next_url:
                url = next_url
            elif page == 1:
                url = self.PAGE1_URL.format(asin=self.ASIN)
            else:
                url = self.BASE_URL.format(asin=self.ASIN, page=page)

            print(f"[Page {page}] Fetching...", end=' ', flush=True)
            self.log(f"Fetching URL: {url}")
            html = self._fetch_page(url, referer=prev_url)
            prev_url = url  # this page becomes the referer for the next
            if not html:
                self.consecutive_empty += 1
                self.log(f"Page {page}: Failed to fetch (Consecutive: {self.consecutive_empty})")
                print("❌ Failed")
                next_url = None  # reset so we retry with constructed URL
            else:
                soup     = BeautifulSoup(html, 'html.parser')
                reviews  = self._parse_page(soup)   # already deduped via self.seen_keys
                next_url = self._get_next_url(soup)  # extract real next-page link
                self.log(f"  Next URL: {next_url}")

                if reviews:
                    self.reviews.extend(reviews)
                    self.last_page = page
                    self.consecutive_empty = 0
                    self.log(f"Page {page}: Found {len(reviews)} new reviews (Buffer: {len(self.reviews)})")
                    print(f"✓ {len(reviews)} new  (buffer: {len(self.reviews)})")
                else:
                    self.consecutive_empty += 1
                    self.log(f"Page {page}: 0 new reviews — all duplicates or empty (Consecutive: {self.consecutive_empty})")
                    print(f"⚠ 0 new reviews — all duplicates (consecutive: {self.consecutive_empty})")

                    page_text = soup.get_text()
                    if ('no customer reviews' in page_text.lower() or
                            'there are 0 reviews' in page_text.lower()):
                        print("\n✅ Amazon confirmed: no more reviews.")
                        self.log("Amazon confirmed: no more reviews.")
                        break

                # No next-page button = we are on the last page
                if not next_url:
                    print("\n✅ No 'next page' button — reached the last page.")
                    self.log(f"No next-page link found on page {page}. End of reviews.")
                    if self.reviews:
                        self._save()
                    break

            # Stop after 5 consecutive empty/duplicate/failed pages
            if self.consecutive_empty >= 5:
                print(f"\n⚠ 5 consecutive empty pages — stopping.")
                self.log(f"STOPPING: 5 consecutive empty pages. Last good page: {self.last_page}")
                break

            # Checkpoint save every 5 pages
            if page % 5 == 0:
                saved = self._save()
                self.reviews = []
                self.log(f"Checkpoint: Saved at page {page}. Total in file: {saved}")
                print(f"\n📊 Saved checkpoint at page {page}. Total in file: {saved}\n")

            page += 1
            time.sleep(random.uniform(8, 14))

        # Final save
        if self.reviews:
            self._save()

    # ------------------------------------------------------------------ save
    def _save(self):
        """APPEND new reviews to CSV — never overwrites existing data."""
        if not self.reviews:
            return self._count_existing()
        try:
            new_df = pd.DataFrame(self.reviews)
            file_exists = os.path.exists(self.CSV_FILE)
            # Append mode: write header only when file doesn't exist yet
            new_df.to_csv(
                self.CSV_FILE,
                mode='a',
                header=not file_exists,
                index=False,
                encoding='utf-8-sig'
            )
            count = self._count_existing()
            self.total_in_file = count
            return count
        except Exception as e:
            self.log(f"Save error: {e}")
            print(f"❌ Save error: {e}")
            return self.total_in_file

    def print_stats(self):
        try:
            df = pd.read_csv(self.CSV_FILE)
            print(f"\n{'='*55}")
            print(f"  FINAL STATISTICS — iphone14_amazon_reviews.csv")
            print(f"{'='*55}")
            print(f"  Total Reviews : {len(df)}")
            print(f"  Rating Distribution:")
            print(df['rating'].value_counts().sort_index().to_string())
            print(f"{'='*55}\n")
        except Exception as e:
            print(f"Could not load stats: {e}")


# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  AMAZON INDIA REVIEW SCRAPER")
    print("  Product : Apple iPhone 14 (ASIN B0BDJS3MRM)")
    print("=" * 55)

    scraper = AmazonReviewScraper()
    scraper.log("=" * 55)

    # ── One-time dedup: clean up any duplicate rows already in the CSV ──
    try:
        df = pd.read_csv(scraper.CSV_FILE)
        before = len(df)
        df = df.drop_duplicates(subset=['title', 'review_text'], keep='first')
        after = len(df)
        if before != after:
            df.to_csv(scraper.CSV_FILE, index=False, encoding='utf-8-sig')
            print(f"🧹 Removed {before - after} duplicate rows. CSV now has {after} unique reviews.")
            scraper.total_in_file = after
        else:
            print(f"✓ CSV is clean ({after} rows, no duplicates)")
    except Exception:
        pass

    # Detect resume point from last SAVED checkpoint (not just last scraped page)
    last = scraper._get_last_checkpoint_page()
    if last > 0:
        # Last checkpoint page is fully saved — resume from the very next page
        resume = last + 1
        scraper.log(f"Resuming — last checkpoint: page {last}, starting from: {resume}")
        print(f"\n▶ Resuming from page {resume}  (last saved checkpoint: page {last})")
    else:
        resume = 1
        scraper.log("Starting fresh scrape — iPhone 14 Amazon reviews")
        print("\n▶ Starting fresh scrape from page 1")

    # Warm up session first
    scraper._init_session(max_wait_min=60)

    # Load existing review keys so we never re-save already-scraped reviews
    scraper._load_seen_keys()

    try:
        scraper.scrape_all(start_page=resume)
        scraper._save()
        scraper.print_stats()
        scraper.log(f"Scraping complete. Total reviews: {scraper.total_in_file}")

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted! Saving...")
        scraper.log("Scraper interrupted by user")
        saved = scraper._save()
        scraper.log(f"Progress saved. Total: {saved}")
        print(f"✓ Saved. Total reviews in file: {saved}")
    except Exception as e:
        scraper.log(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        scraper._save()


if __name__ == "__main__":
    main()
