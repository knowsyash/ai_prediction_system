# YouTube Comment Scraper - English Comments

Enhanced scraper with checkpoint saving, resume capability, and detailed logging.

## Target Video
- **URL**: https://www.youtube.com/watch?v=xRla0izRxqU
- **Output**: `english_yt_comments.csv`
- **Log File**: `scraping_log.txt`

## Features

### 🔄 Auto-Save Checkpoints
- Automatically saves comments every 50 comments
- Prevents data loss if scraping is interrupted
- Memory efficient - clears batch after each save

### 📝 Detailed Logging
- Maintains `scraping_log.txt` with timestamp logs
- Tracks:
  - Total comments scraped
  - Checkpoint saves
  - Errors and interruptions
  - Session start/end times

### 🔁 Resume Capability
- Automatically resumes from where it left off
- Skips duplicate comments using comment_id
- Shows existing comment count on restart

### 🛡️ Duplicate Prevention
- Tracks all comment IDs in the CSV
- Skips already-scraped comments
- Reports number of duplicates skipped

### ⚠️ Error Handling
- Saves progress before exit on errors
- Handles keyboard interruption (Ctrl+C) gracefully
- Automatic error logging

## Installation

```powershell
# Activate virtual environment (from project root)
cd "c:\Users\yashs\Desktop\MINOR 2"
.\.venv\Scripts\Activate.ps1

# Install required package
pip install youtube-comment-downloader
```

## Usage

### First Run
```powershell
cd "YOUTUBE\data_scrapping\english_comments"
python youtube_comment_scraper.py
```

The scraper will:
1. Create `english_yt_comments.csv` if not present
2. Start scraping comments
3. Save every 50 comments automatically
4. Log progress to `scraping_log.txt`

### Resume After Interruption
Just run the same command again:
```powershell
python youtube_comment_scraper.py
```

The scraper will:
- Read existing comments from CSV
- Skip already-scraped comments
- Continue from where it left off
- Show "Skipped X duplicate comments" message

## Output Files

### 1. `english_yt_comments.csv`
Main data file with columns:
- `comment_id` - Unique identifier
- `author` - Commenter name
- `text` - Comment text
- `time` - When posted (relative)
- `likes` - Number of likes (handles 1.2k format)
- `is_reply` - True if reply to another comment
- `parent_id` - Parent comment ID (if reply)
- `scraped_at` - When scraped

### 2. `scraping_log.txt`
Detailed log file with:
```
[2026-03-04 20:52:15] Starting scrape session for video: xRla0izRxqU
[2026-03-04 20:52:45] Checkpoint: Saved 50 new comments. Total in file: 50
[2026-03-04 20:53:15] Checkpoint: Saved 50 new comments. Total in file: 100
...
```

### 3. `english_yt_comments.json`
JSON backup of all comments

## Example Output

```
Starting to scrape comments from video: xRla0izRxqU
Video URL: https://www.youtube.com/watch?v=xRla0izRxqU
Resuming scrape - Existing comments in file: 350
----------------------------------------------------------------------
✓ Scraped 50 new comments (Total in file: 400, Skipped duplicates: 12)
✓ Scraped 100 new comments (Total in file: 450, Skipped duplicates: 25)
...

✓ Successfully scraped 150 new comments!
✓ Total comments in file: 500
✓ Skipped 28 duplicate comments

======================================================================
FINAL SCRAPING STATISTICS
======================================================================
Total Comments: 500
Top-level Comments: 425
Replies: 75
Total Likes: 8,542
Average Likes per Comment: 17.08
Most Liked Comment: 1200 likes
Output File: english_yt_comments.csv
======================================================================
```

## Troubleshooting

### If scraping stops unexpectedly
The progress is automatically saved. Just run the script again:
```powershell
python youtube_comment_scraper.py
```

### To start fresh (delete existing data)
```powershell
Remove-Item english_yt_comments.csv
Remove-Item scraping_log.txt
python youtube_comment_scraper.py
```

### Check progress without running scraper
```powershell
# View current comment count
Get-Content english_yt_comments.csv | Measure-Object -Line

# View recent log entries
Get-Content scraping_log.txt -Tail 20
```

## Notes

- The scraper saves every 50 comments to prevent data loss
- Duplicate detection is based on `comment_id`
- Log file grows with each run - review periodically
- Press Ctrl+C to stop gracefully (will save current batch)
- CSV file is created at the start if not present
- All timestamps are in local time (IST)
