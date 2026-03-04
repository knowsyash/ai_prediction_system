"""Convert JSON comments to properly formatted CSV"""

import pandas as pd
import json

def convert_json_to_csv():
    print("Converting JSON to CSV...")
    
    # Read the JSON file
    with open('iphone_youtube_comments.json', 'r', encoding='utf-8') as f:
        comments = json.load(f)
    
    # Convert likes to integer
    for comment in comments:
        try:
            likes = comment.get('likes', 0)
            if isinstance(likes, str):
                # Handle string formats like '3.4k', '892', etc.
                if 'k' in likes.lower():
                    comment['likes'] = int(float(likes.lower().replace('k', '')) * 1000)
                else:
                    comment['likes'] = int(likes)
            else:
                comment['likes'] = int(likes) if likes else 0
        except:
            comment['likes'] = 0
    
    # Create DataFrame
    df = pd.DataFrame(comments)
    
    # Reorder columns
    columns_order = ['comment_id', 'author', 'text', 'time', 'likes', 
                    'is_reply', 'parent_id', 'scraped_at']
    df = df[columns_order]
    
    # Save to CSV
    df.to_csv('iphone_youtube_comments.csv', index=False, encoding='utf-8-sig')
    
    print(f"✓ Converted {len(df)} comments to CSV")
    print("\nStatistics:")
    print(f"Total Comments: {len(df)}")
    print(f"Top-level Comments: {len(df[df['is_reply'] == False])}")
    print(f"Replies: {len(df[df['is_reply'] == True])}")
    print(f"Total Likes: {df['likes'].sum()}")
    print(f"Average Likes: {df['likes'].mean():.2f}")
    print(f"Max Likes: {df['likes'].max()}")

if __name__ == "__main__":
    convert_json_to_csv()
