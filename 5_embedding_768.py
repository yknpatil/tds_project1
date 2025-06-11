import os
import json
import requests

# Get API token from environment
API_TOKEN = os.getenv("JINA_API_KEY")
if not API_TOKEN:
    raise ValueError("JINA_API_KEY environment variable is not set")

print(f"DEBUG: Using JINA_API_KEY = {API_TOKEN[:10]}...")  

# Jina embedding endpoint
API_URL = "https://api.jina.ai/v1/embeddings"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Windows paths via WSL (adjust if using native Windows Python)
input_path = "/mnt/c/Users/user/Documents/TDS_Project1/all_course_data.json"
output_path = "/mnt/c/Users/user/Documents/TDS_Project1/embedded_data_768.json"

# Optional: Limit text size to avoid token overflow
MAX_TOKENS = 512

def truncate_text(text, max_tokens=MAX_TOKENS):
    return " ".join(text.split()[:max_tokens])

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_embedding(input_data, input_type="text"):
    if input_type == "text":
        payload = {
            "model": "jina-embeddings-v2-base-en",
            "input": input_data
        }
    elif input_type == "image":
        payload = {
            "model": "jina-clip-v2",
            "input": {
                "image_url": input_data
            }
        }
    else:
        raise ValueError("input_type must be 'text' or 'image'")

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        print(f"Response content: {response.text}")
        raise

    response_json = response.json()
    print("API response:", response_json)  # DEBUG

    if "data" not in response_json or not response_json["data"]:
        raise KeyError(f"No embedding data returned: {response_json}")

    embedding = response_json["data"][0]["embedding"]
    print(f"Embedding length: {len(embedding)}")  # Verify dimension

    return embedding


#This is for all_course_data.json
def main():
    data = load_json(input_path)
    embedded_data = {}

    for filename, content in data.items():
        if content:
            try:
                truncated_content = truncate_text(content)
                embedding = get_embedding(truncated_content, input_type="text")
                embedded_data[filename] = {
                    "content": content,
                    "embedding": embedding
                }
            except Exception as e:
                print(f"Failed to embed {filename}: {e}")
                embedded_data[filename] = {
                    "content": content,
                    "embedding": None,
                    "error": str(e)
                }
        else:
            embedded_data[filename] = {
                "content": content,
                "embedding": None
            }

    save_json(embedded_data, output_path)
    print(f"\n Embedding data saved to {output_path}")

"""
#This is for discourse_posts_2025.json
def main():
    data = load_json(input_path)  # data is a list of threads
    embedded_data = {}

    for thread in data:
        thread_title = thread.get("title", "untitled_thread")
        posts = thread.get("posts", [])
        
        for i, post in enumerate(posts):
            content_html = post.get("content_html", "")
            print(f"Content causing error: {content_html[:200]}")
            key = f"{thread_title}_post_{i}"
            if content_html:
                try:
                    truncated_content = truncate_text(content_html)
                    embedding = get_embedding(truncated_content, input_type="text")
                    # Create a unique key for storage, e.g., thread_title + post number
                    key = f"{thread_title}_post_{i}"
                    embedded_data[key] = {
                        "content_html": content_html,
                        "embedding": embedding
                    }
                except Exception as e:
                    print(f"Failed to embed post {i} in thread '{thread_title}': {e}")
                    embedded_data[key] = {
                        "content_html": content_html,
                        "embedding": None,
                        "error": str(e)
                    }
            else:
                embedded_data[key] = {
                    "content_html": content_html,
                    "embedding": None
                }

    save_json(embedded_data, output_path)
    print(f"\n Embedding data saved to {output_path}")
"""

if __name__ == "__main__":
    main()
