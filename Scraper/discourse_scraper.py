import requests
from datetime import datetime, timezone
import json
import time
import os
from bs4 import BeautifulSoup

DISCOURSE_BASE = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = "34"
SESSION_COOKIE = "N85E9CuEGcfsybSUbGLBXg%2FnMJJEAzIhrJRaGHWkO44892XexbRbo0jGXwNN3kUn8Avip2crWb3a8vWl%2FL9VHU0oAAW6UYHKdB%2B%2Fp%2BWib3W85qcf0%2FyhKkLlh4zet1oC29yFDQpWAN3LmZlWz3jl1PTZcwiFrGJYWlp2C6dXorkWuW61QleuGVOiFd7RQy%2B9ix54GxqrC6R4a7PtlTaolmAyrWNPuQJbwPmMA%2FoTd1GZGFDaUdGRGnz09d9T1hN3SVMW6Psck7X6Qnuw3JlJygliHg0pCyJH9AR3X7PLxe%2FyAKCtpWVTMr5%2FahE%3D--o3CaAnh4kixoMzkm--aXdSuXB2c%2FKhQq022ynZ5Q%3D%3D"
START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 4, 14, tzinfo=timezone.utc)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Cookie': f'_t={SESSION_COOKIE}'
}

def get_topic_content(topic_id, topic_slug):
    """Fetch actual content from individual topic"""
    try:
        # Use the individual topic endpoint to get full content
        url = f"{DISCOURSE_BASE}/t/{topic_slug}/{topic_id}.json"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"    ❌ Failed to fetch topic {topic_id}: {response.status_code}")
            return None
            
        topic_data = response.json()
        
        # Get the first post (original post) content
        if topic_data.get('post_stream') and topic_data['post_stream'].get('posts'):
            first_post = topic_data['post_stream']['posts'][0]
            
            # Extract clean text from HTML
            soup = BeautifulSoup(first_post.get('cooked', ''), 'html.parser')
            clean_content = soup.get_text(separator='\n', strip=True)
            
            return {
                'title': topic_data.get('title', 'No title'),
                'content': clean_content[:500] + '...' if len(clean_content) > 500 else clean_content,  # Limit content
                'full_content': clean_content,
                'url': f"{DISCOURSE_BASE}/t/{topic_slug}/{topic_id}",
                'date': first_post.get('created_at'),
                'replies': topic_data.get('reply_count', 0),
                'category': topic_data.get('category_id'),
                'author': first_post.get('username', 'Unknown')
            }
    except Exception as e:
        print(f"    ❌ Error fetching topic {topic_id}: {e}")
        return None

def scrape_discourse_posts():
    print("🚀 Scraping Discourse forum...")
    all_posts = []
    page = 0
    
    # Step 1: Get topic list from category
    while page < 10:  # Limit for testing
        url = f"{DISCOURSE_BASE}/c/courses/tds-kb/{CATEGORY_ID}.json?page={page}"
        print(f"📃 Fetching topic list page {page}...")
        
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch page {page}")
            break
            
        try:
            data = response.json()
        except:
            print("❌ Invalid JSON response")
            break
            
        topics = data.get('topic_list', {}).get('topics', [])
        print(f"Found {len(topics)} topics on page {page}")
        
        if not topics:
            break
            
        # Step 2: Process each topic
        for i, topic in enumerate(topics):
            try:
                # Parse date
                created_at_str = topic['created_at']
                if created_at_str.endswith('Z'):
                    created_at_str = created_at_str[:-1] + '+00:00'
                
                created_at = datetime.fromisoformat(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                
                print(f"  📄 Topic {i+1}: {topic.get('title', 'No title')[:50]}... - {created_at.date()}")
                
                # Check date range
                if START_DATE <= created_at <= END_DATE:
                    print(f"    ✅ Within date range, fetching content...")
                    
                    # Fetch actual content
                    topic_content = get_topic_content(topic.get('id'), topic.get('slug', ''))
                    
                    if topic_content:
                        all_posts.append(topic_content)
                        print(f"    ✅ Added post with {len(topic_content['content'])} characters")
                    
                    # Rate limiting - be nice to the server
                    time.sleep(2)
                else:
                    print(f"    ⏭️  Outside date range")
                    
            except Exception as e:
                print(f"    ❌ Error processing topic: {e}")
                continue
        
        page += 1
        time.sleep(1)
    
    print(f"✅ Scraped {len(all_posts)} posts with actual content")
    return all_posts

if __name__ == "__main__":
    data = scrape_discourse_posts()
    
    os.makedirs('../data', exist_ok=True)
    with open('../data/discourse_posts.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("💾 Data saved to ../data/discourse_posts.json")
    print(f"📊 Total posts with content: {len(data)}")
    
    # Show sample of what we got
    if data:
        print("\n📋 Sample post:")
        sample = data[0]
        print(f"Title: {sample['title']}")
        print(f"Content preview: {sample['content'][:100]}...")
        print(f"Author: {sample['author']}")
