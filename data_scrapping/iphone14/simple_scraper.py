"""iPhone 14 Flipkart Review Scraper — single fetch, parse all cards"""

from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

URL      = "https://www.flipkart.com/apple-iphone-14-starlight-128-gb/product-reviews/itm3485a56f6e676?pid=MOBGHWFHABH3G73H&marketplace=FLIPKART"
CSV_FILE = "iphone14_reviews.csv"

def fetch(url):
    session = requests.Session(impersonate="chrome131")
    resp = session.get(url, headers={"Accept-Language": "en-IN,en-GB;q=0.9"}, timeout=30)
    resp.raise_for_status()
    return resp.text

def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="fWi7J_")
    reviews = []

    for card in cards:
        text = card.get_text(separator=" ", strip=True)

        # Must start with a rating digit
        m = re.match(r'^([1-5](?:\.\d)?)\s*[•·]\s*(.+)', text)
        if not m:
            continue

        rating_str, rest = m.group(1), m.group(2)

        if "ratings and" in rest or "User reviews sorted" in rest:
            continue

        # Title = text before "Review for:"
        tm = re.match(r'^(.+?)\s+Review for:', rest)
        if tm:
            title       = tm.group(1).strip()
            review_body = rest[tm.end():].strip()
        else:
            parts       = rest.split("  ", 1)
            title       = parts[0].strip()
            review_body = parts[1].strip() if len(parts) > 1 else ""

        # Strip "Color X • Storage X GB" spec line
        review_body = re.sub(r'^Color\s+\S+.*?GB\s*', '', review_body).strip()

        # Strip trailing noise (name, city, Helpful, Verified, date)
        review_body = re.sub(r'\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*,\s*[A-Z][a-z].*$', '', review_body).strip()
        review_body = re.sub(r'\s*(Helpful|Verified Purchase|READ MORE|Report Abuse).*$', '', review_body, flags=re.IGNORECASE).strip()

        title       = re.sub(r'\s+', ' ', title).strip()
        review_body = re.sub(r'\s+', ' ', review_body).strip()

        try:
            rating = int(float(rating_str))
        except ValueError:
            continue

        if len(title) < 2 or len(review_body) < 10:
            continue

        reviews.append({"rating": rating, "title": title, "review_text": review_body})

    return reviews

if __name__ == "__main__":
    print("Fetching page...")
    html = fetch(URL)

    reviews = parse(html)
    print(f"Parsed {len(reviews)} reviews")

    if reviews:
        df = pd.DataFrame(reviews).drop_duplicates(subset=["title", "review_text"])
        df.to_csv(CSV_FILE, index=False)
        print(f"Saved to {CSV_FILE}")
        print(df["rating"].value_counts().sort_index().to_string())
    else:
        print("No reviews found.")
