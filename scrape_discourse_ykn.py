import requests
import json
import os
from datetime import datetime
import time

# Session cookie from browser
COOKIE = '***'  # <-- replace with full cookie
HEADERS = {
    'Cookie': COOKIE,
    'User-Agent': 'Mozilla/5.0'
}

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_URL = f"{BASE_URL}/c/courses/tds-kb/34.json"
TOPIC_URL_TEMPLATE = f"{BASE_URL}/t/{{}}.json"

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 4, 14)

# Output path (adjusted for WSL)
OUTPUT_PATH = "/mnt/c/Users/user/Documents/TDS_Project1/"
OUTPUT_FILE = os.path.join(OUTPUT_PATH, "discourse_posts_2025.json")

def fetch_category_topics(page=0):
    url = f"{CATEGORY_URL}?page={page}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to get page {page}: {response.status_code}")
        return []
    data = response.json()
    return data.get("topic_list", {}).get("topics", [])

def fetch_topic_details(topic_id):
    url = TOPIC_URL_TEMPLATE.format(topic_id)
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch topic {topic_id}: {response.status_code}")
        return None
    return response.json()

def is_within_date_range(date_str):
    date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
    return START_DATE <= date_obj <= END_DATE

def main():
    page = 0
    all_posts = []

    while True:
        print(f"Fetching page {page}...")
        topics = fetch_category_topics(page)
        if not topics:
            break

        for topic in topics:
            if is_within_date_range(topic['created_at']):
                topic_id = topic['id']
                topic_data = fetch_topic_details(topic_id)
                if topic_data:
                    topic_info = {
                        "title": topic_data['title'],
                        "id": topic_id,
                        "posts": []
                    }
                    for post in topic_data['post_stream']['posts']:
                        if is_within_date_range(post['created_at']):
                            topic_info["posts"].append({
                                "username": post['username'],
                                "created_at": post['created_at'],
                                "content_html": post['cooked']
                            })
                    all_posts.append(topic_info)
        page += 1
        time.sleep(1)

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"\n Data saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()


