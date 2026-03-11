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
        self.progress_file = 'scraping_log.txt'
        self.session_start_count = self._count_existing_comments()
        self.total_scraped = self.session_start_count
        self.existing_comment_ids = self._get_existing_comment_ids()
        
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
    
    def _count_existing_comments(self):
        """Count comments already in the CSV file"""
        try:
            df = pd.read_csv(self.output_filename)
            return len(df)
        except:
            return 0
    
    def _get_existing_comment_ids(self):
        """Get set of existing comment IDs to prevent duplicates"""
        try:
            df = pd.read_csv(self.output_filename)
            return set(df['comment_id'].astype(str).tolist())
        except:
            return set()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.output_filename):
            df = pd.DataFrame(columns=['comment_id', 'author', 'text', 'time', 'time_parsed', 
                                      'likes', 'is_reply', 'parent_id', 'scraped_at'])
            df.to_csv(self.output_filename, index=False, encoding='utf-8-sig')
    
    def _log_progress(self, message):
        """Log progress messages to file"""
        try:
            with open(self.progress_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except:
            pass
    
    def scrape_with_downloader(self, max_comments=None, sort_by=None):
        """Scrape comments using youtube-comment-downloader library"""
        if not DOWNLOADER_AVAILABLE:
            print("ERROR: youtube-comment-downloader not available")
            return False
        
        if sort_by is None:
            sort_by = SORT_BY_RECENT
        
        try:
            # Initialize CSV file if not present
            self._initialize_csv()
            
            print(f"Starting to scrape comments from video: {self.video_id}")
            print(f"Video URL: {self.video_url}")
            if self.session_start_count > 0:
                print(f"Resuming scrape - Existing comments in file: {self.session_start_count}")
            print("-" * 70)
            
            self._log_progress("=" * 70)
            self._log_progress(f"Starting scrape session for video: {self.video_id}")
            self._log_progress(f"Existing comments in file: {self.session_start_count}")
            
            downloader = YoutubeCommentDownloader()
            comments_generator = downloader.get_comments_from_url(
                self.video_url, 
                sort_by=sort_by
            )
            
            new_count = 0
            skipped_duplicates = 0
            
            for comment in comments_generator:
                comment_id = comment.get('cid', '')
                
                # Skip if already scraped
                if comment_id in self.existing_comment_ids:
                    skipped_duplicates += 1
                    continue
                
                new_count += 1
                
                # Handle likes - convert "1.2k" format to integer
                likes_raw = comment.get('votes', 0)
                try:
                    if isinstance(likes_raw, str):
                        if 'k' in likes_raw.lower():
                            likes = int(float(likes_raw.lower().replace('k', '')) * 1000)
                        elif 'm' in likes_raw.lower():
                            likes = int(float(likes_raw.lower().replace('m', '')) * 1000000)
                        else:
                            likes = int(likes_raw)
                    else:
                        likes = int(likes_raw) if likes_raw else 0
                except:
                    likes = 0
                
                # Extract relevant information
                comment_data = {
                    'comment_id': comment_id,
                    'author': comment.get('author', ''),
                    'text': comment.get('text', ''),
                    'time': comment.get('time', ''),
                    'time_parsed': comment.get('time_parsed', ''),
                    'likes': likes,
                    'is_reply': comment.get('reply', False),
                    'parent_id': comment.get('parent', ''),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.comments.append(comment_data)
                self.existing_comment_ids.add(comment_id)
                
                # Auto-save checkpoint every 50 comments
                if new_count % 50 == 0:
                    saved_count = self._save_checkpoint()
                    self.total_scraped = saved_count
                    self._log_progress(f"Checkpoint: Saved {new_count} new comments. Total in file: {saved_count}")
                    print(f"✓ Scraped {new_count} new comments (Total in file: {saved_count}, Skipped duplicates: {skipped_duplicates})")
                
                # Check if we've reached max comments
                if max_comments and new_count >= max_comments:
                    print(f"Reached maximum comment limit: {max_comments}")
                    self._log_progress(f"Reached maximum comment limit: {max_comments}")
                    break
                
                # Small delay to be respectful
                if new_count % 100 == 0:
                    time.sleep(1)
            
            # Final save
            if self.comments:
                final_count = self._save_checkpoint()
                self.total_scraped = final_count
            
            print(f"\n✓ Successfully scraped {new_count} new comments!")
            print(f"✓ Total comments in file: {self.total_scraped}")
            if skipped_duplicates > 0:
                print(f"✓ Skipped {skipped_duplicates} duplicate comments")
            
            self._log_progress(f"Scraping session completed. New comments: {new_count}, Total: {self.total_scraped}, Skipped duplicates: {skipped_duplicates}")
            self._log_progress("=" * 70)
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user! Saving progress...")
            self._log_progress("Scraping interrupted by user")
            if self.comments:
                saved_count = self._save_checkpoint()
                print(f"✓ Progress saved. Total comments in file: {saved_count}")
                self._log_progress(f"Progress saved before interruption. Total: {saved_count}")
            return False
            
        except Exception as e:
            error_msg = f"Error during scraping: {str(e)}"
            print(error_msg)
            self._log_progress(error_msg)
            # Try to save what we have
            if self.comments:
                saved_count = self._save_checkpoint()
                print(f"Saved {len(self.comments)} comments before error. Total: {saved_count}")
                self._log_progress(f"Saved comments before error. Total: {saved_count}")
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
    
    def _save_checkpoint(self):
        """Save current batch of comments to CSV and clear memory"""
        if not self.comments:
            return self._count_existing_comments()
        
        try:
            # Load existing data
            try:
                existing_df = pd.read_csv(self.output_filename)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                existing_df = pd.DataFrame()
            
            # Append new comments
            new_df = pd.DataFrame(self.comments)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Save to CSV
            combined_df.to_csv(self.output_filename, index=False, encoding='utf-8-sig')
            
            # Clear memory
            total_count = len(combined_df)
            self.comments = []
            
            return total_count
            
        except Exception as e:
            print(f"Error saving checkpoint: {str(e)}")
            return self._count_existing_comments()
    
    def save_to_csv(self):
        """Final save and display statistics"""
        try:
            # Ensure all comments are saved
            if self.comments:
                self._save_checkpoint()
            
            # Load full dataset for statistics
            df = pd.read_csv(self.output_filename)
            
            if len(df) == 0:
                print("No comments in file!")
                return False
            
            # Print statistics
            print("\n" + "=" * 70)
            print("FINAL SCRAPING STATISTICS")
            print("=" * 70)
            print(f"Total Comments: {len(df)}")
            print(f"Top-level Comments: {len(df[df['is_reply'] == False])}")
            print(f"Replies: {len(df[df['is_reply'] == True])}")
            print(f"Total Likes: {df['likes'].sum()}")
            print(f"Average Likes per Comment: {df['likes'].mean():.2f}")
            print(f"Most Liked Comment: {df['likes'].max()} likes")
            print(f"Output File: {self.output_filename}")
            print("=" * 70)
            
            self._log_progress(f"Final statistics - Total: {len(df)}, Top-level: {len(df[df['is_reply'] == False])}, Replies: {len(df[df['is_reply'] == True])}")
            
            return True
            
        except Exception as e:
            print(f"Error displaying statistics: {str(e)}")
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
    
    def scrape_with_api(self, api_key, max_comments=100):
        """Scrape comments using YouTube Data API v3"""
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


def main():
    """Main function to run the scraper"""
    
    # Video URL - UPDATED TO NEW VIDEO
    VIDEO_URL = "https://www.youtube.com/watch?v=GVqTlrV7eL8"
    
    # Output filename
    OUTPUT_FILE = "samsung25.csv"
    
    print("=" * 70)
    print("YOUTUBE COMMENT SCRAPER - ENGLISH COMMENTS")
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
            scraper.save_to_csv()  # Display final statistics
            scraper.save_to_json()  # Save JSON backup
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
