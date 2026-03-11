# YouTube Comment Scraper

This scraper extracts comments from YouTube videos for sentiment analysis and data processing.

## Target Video
- **URL**: https://www.youtube.com/watch?v=kBDCkoCxkrg&t=141s
- **Output**: `iphone_youtube_comments.csv`

## Installation

### Option 1: Using the project virtual environment
```powershell
# Activate the virtual environment (from project root)
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Option 2: Install individually
```powershell
pip install youtube-comment-downloader
pip install pandas
pip install google-api-python-client  # Optional, for API method
```

## Usage

### Method 1: Simple Scraping (No API Key Required) - RECOMMENDED
```powershell
python youtube_comment_scraper.py
```

This method uses the `youtube-comment-downloader` library and doesn't require any API keys. It will scrape all available comments from the video.

### Method 2: Using YouTube Data API (Requires API Key)
If you prefer to use the official YouTube API:

1. Get an API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3
3. Edit the script and uncomment the API method:

```python
API_KEY = 'YOUR_API_KEY_HERE'
scraper.scrape_with_api(API_KEY, max_comments=1000)
```

## Output Format

The scraper generates a CSV file with the following columns:
- `comment_id`: Unique comment identifier
- `author`: Comment author's display name
- `text`: The comment text
- `time`: Timestamp when comment was posted
- `likes`: Number of likes on the comment
- `is_reply`: Boolean indicating if it's a reply to another comment
- `parent_id`: ID of parent comment (if it's a reply)
- `scraped_at`: Timestamp when the comment was scraped

## Features

- ✅ Scrapes all comments and replies
- ✅ No API key required (Method 1)
- ✅ Progress tracking during scraping
- ✅ Saves to CSV and JSON formats
- ✅ Detailed statistics after scraping
- ✅ Error handling and retry logic
- ✅ Respectful rate limiting

## Troubleshooting

### "youtube-comment-downloader not installed"
```powershell
pip install youtube-comment-downloader
```

### ModuleNotFoundError
Make sure you're in the correct directory and have activated the virtual environment:
```powershell
cd "c:\Users\yashs\Desktop\MINOR 2\YOU TUBE\data_scrapping"
..\..\..\.venv\Scripts\Activate.ps1
```

## Notes

- The scraper includes small delays between requests to be respectful to YouTube's servers
- Progress is saved periodically in `scraping_progress.txt`
- Both CSV and JSON outputs are created for backup
- The script will display statistics after scraping completes
