"""YouTube Comment Scraper - Simple and Effective"""

import pandas as pd
import time
import json
from datetime import datetime
import os

try:
    from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT
    DOWNLOADER_AVAILABLE = True
except ImportError:
    DOWNLOADER_AVAILABLE = False
    print("youtube-comment-downloader not installed. Install with: pip install youtube-comment-downloader")

try:
    from googleapiclient.discovery import build
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

class YouTubeCommentScraper:
    def __init__(self, video_url, output_filename='youtube_comments.csv'):
        """
        Initialize the YouTube Comment Scraper
        
        Args:
            video_url: Full YouTube video URL
            output_filename: Name of the CSV file to save comments
        """
        self.video_url = video_url
        self.video_id = self._extract_video_id(video_url)
        self.output_filename = output_filename
        self.comments = []
        self.progress_file = 'scraping_progress.txt'
        
    def _extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        if 'v=' in url:
            video_id = url.split('v=')[1]
            # Remove any additional parameters
            if '&' in video_id:
                video_id = video_id.split('&')[0]
            return video_id
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1]
            if '?' in video_id:
                video_id = video_id.split('?')[0]
            return video_id
        return None
    
    def scrape_with_downloader(self, max_comments=None, sort_by=SORT_BY_RECENT):
        """
        Scrape comments using youtube-comment-downloader library
        This method doesn't require API keys
        
        Args:
            max_comments: Maximum number of comments to scrape (None for all)
            sort_by: SORT_BY_RECENT or SORT_BY_POPULAR
        """
        if not DOWNLOADER_AVAILABLE:
            print("ERROR: youtube-comment-downloader library not available")
            print("Install it using: pip install youtube-comment-downloader")
            return False
        
        try:
            print(f"Starting to scrape comments from video: {self.video_id}")
            print(f"Video URL: {self.video_url}")
            print("-" * 70)
            
            downloader = YoutubeCommentDownloader()
            comments_generator = downloader.get_comments_from_url(
                self.video_url, 
                sort_by=sort_by
            )
            
            count = 0
            for comment in comments_generator:
                count += 1
                
                # Extract relevant information
                comment_data = {
                    'comment_id': comment.get('cid', ''),
                    'author': comment.get('author', ''),
                    'text': comment.get('text', ''),
                    'time': comment.get('time', ''),
                    'time_parsed': comment.get('time_parsed', ''),
                    'likes': int(comment.get('votes', 0)) if comment.get('votes', 0) else 0,
                    'is_reply': comment.get('reply', False),
                    'parent_id': comment.get('parent', ''),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.comments.append(comment_data)
                
                # Progress update
                if count % 50 == 0:
                    print(f"Scraped {count} comments...")
                    self._save_progress(count)
                
                # Check if we've reached max comments
                if max_comments and count >= max_comments:
                    print(f"Reached maximum comment limit: {max_comments}")
                    break
                
                # Small delay to be respectful
                if count % 100 == 0:
                    time.sleep(1)
            
            print(f"\n✓ Successfully scraped {count} comments!")
            return True
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return False
    
    def scrape_with_api(self, api_key, max_comments=100):
        """
        Scrape comments using YouTube Data API v3
        Requires an API key from Google Cloud Console
        
        Args:
            api_key: Your YouTube Data API v3 key
            max_comments: Maximum number of comments to retrieve
        """
        if not YOUTUBE_API_AVAILABLE:
            print("ERROR: Google API client library not available")
            print("Install it using: pip install google-api-python-client")
            return False
        
        try:
            print(f"Starting API-based scraping for video: {self.video_id}")
            print("-" * 70)
            
            youtube = build('youtube', 'v3', developerKey=api_key)
            
            # Get video details first
            video_response = youtube.videos().list(
                part='snippet,statistics',
                id=self.video_id
            ).execute()
            
            if video_response['items']:
                video_info = video_response['items'][0]
                print(f"Video Title: {video_info['snippet']['title']}")
                print(f"Channel: {video_info['snippet']['channelTitle']}")
                print(f"Total Comments: {video_info['statistics'].get('commentCount', 'N/A')}")
                print("-" * 70)
            
            # Get comments
            count = 0
            next_page_token = None
            
            while count < max_comments:
                request = youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=self.video_id,
                    maxResults=min(100, max_comments - count),
                    pageToken=next_page_token,
                    textFormat='plainText'
                )
                
                response = request.execute()
                
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    
                    comment_data = {
                        'comment_id': item['id'],
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'time': comment['publishedAt'],
                        'time_parsed': comment['publishedAt'],
                        'likes': comment['likeCount'],
                        'is_reply': False,
                        'parent_id': '',
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    self.comments.append(comment_data)
                    count += 1
                    
                    # Get replies if available
                    if 'replies' in item:
                        for reply in item['replies']['comments']:
                            reply_snippet = reply['snippet']
                            reply_data = {
                                'comment_id': reply['id'],
                                'author': reply_snippet['authorDisplayName'],
                                'text': reply_snippet['textDisplay'],
                                'time': reply_snippet['publishedAt'],
                                'time_parsed': reply_snippet['publishedAt'],
                                'likes': reply_snippet['likeCount'],
                                'is_reply': True,
                                'parent_id': item['id'],
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            self.comments.append(reply_data)
                            count += 1
                
                print(f"Scraped {count} comments...")
                
                # Check for next page
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                
                time.sleep(0.5)  # Rate limiting
            
            print(f"\n✓ Successfully scraped {count} comments using API!")
            return True
            
        except Exception as e:
            print(f"Error during API scraping: {str(e)}")
            return False
    
    def _save_progress(self, count):
        """Save scraping progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                f.write(f"Last scraped: {count} comments at {datetime.now()}\n")
                f.write(f"Video ID: {self.video_id}\n")
        except:
            pass
    
    def save_to_csv(self):
        """Save scraped comments to CSV file"""
        if not self.comments:
            print("No comments to save!")
            return False
        
        try:
            df = pd.DataFrame(self.comments)
            
            # Reorder columns for better readability
            columns_order = ['comment_id', 'author', 'text', 'time', 'likes', 
                           'is_reply', 'parent_id', 'scraped_at']
            df = df[columns_order]
            
            df.to_csv(self.output_filename, index=False, encoding='utf-8-sig')
            print(f"\n✓ Saved {len(self.comments)} comments to {self.output_filename}")
            
            # Print statistics
            print("\n" + "=" * 70)
            print("SCRAPING STATISTICS")
            print("=" * 70)
            print(f"Total Comments: {len(df)}")
            print(f"Top-level Comments: {len(df[df['is_reply'] == False])}")
            print(f"Replies: {len(df[df['is_reply'] == True])}")
            print(f"Total Likes: {df['likes'].sum()}")
            print(f"Average Likes per Comment: {df['likes'].mean():.2f}")
            print(f"Most Liked Comment: {df['likes'].max()} likes")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
            return False
    
    def save_to_json(self, filename=None):
        """Save comments to JSON file as backup"""
        if not self.comments:
            return False
        
        if filename is None:
            filename = self.output_filename.replace('.csv', '.json')
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.comments, f, ensure_ascii=False, indent=2)
            print(f"✓ Also saved backup to {filename}")
            return True
        except Exception as e:
            print(f"Error saving JSON: {str(e)}")
            return False


def main():
    """Main function to run the scraper"""
    
    # Video URL
    VIDEO_URL = "https://www.youtube.com/watch?v=kBDCkoCxkrg&t=141s"
    
    # Output filename
    OUTPUT_FILE = "iphone_youtube_comments.csv"
    
    print("=" * 70)
    print("YOUTUBE COMMENT SCRAPER")
    print("=" * 70)
    print(f"Target Video: {VIDEO_URL}")
    print(f"Output File: {OUTPUT_FILE}")
    print("=" * 70)
    print()
    
    # Initialize scraper
    scraper = YouTubeCommentScraper(VIDEO_URL, OUTPUT_FILE)
    
    # Method 1: Using youtube-comment-downloader (No API key needed)
    print("METHOD 1: Using youtube-comment-downloader (Recommended)")
    print("Note: Install with: pip install youtube-comment-downloader")
    print()
    
    if DOWNLOADER_AVAILABLE:
        success = scraper.scrape_with_downloader(
            max_comments=None,  # Set to None for all comments, or specify a number
            sort_by=SORT_BY_RECENT
        )
        
        if success:
            scraper.save_to_csv()
            scraper.save_to_json()
    else:
        print("youtube-comment-downloader not available, skipping Method 1")
        print()
        print("To use Method 2 (YouTube API):")
        print("1. Get an API key from Google Cloud Console")
        print("2. Enable YouTube Data API v3")
        print("3. Uncomment the API method below and add your key")
        print()
        print("# Example:")
        print("# API_KEY = 'YOUR_API_KEY_HERE'")
        print("# scraper.scrape_with_api(API_KEY, max_comments=1000)")
        print("# scraper.save_to_csv()")


if __name__ == "__main__":
    main()
