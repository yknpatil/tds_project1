import requests
import re
import json
import os

BASE_URL = "https://tds.s-anand.net/"
SAVE_DIR = r"C:\Users\user\Documents\TDS_Project1\scrape_course_data" #saved to local
JSON_FILENAME = "all_course_data.json"

def get_sidebar():
    r = requests.get(BASE_URL + "_sidebar.md")
    r.raise_for_status()
    return r.text

def extract_md_links(sidebar_md):
    # Matches markdown links like: [Title](filename.md)
    return re.findall(r"\]\(([^)]+\.md)\)", sidebar_md)

def fetch_md_content(file):
    url = BASE_URL + file
    r = requests.get(url)
    if r.status_code == 200:
        return r.text
    else:
        print(f" Failed to fetch {file}")
        return None

def main():
    sidebar = get_sidebar()
    md_files = extract_md_links(sidebar)

    all_data = {}
    for md_file in md_files:
        content = fetch_md_content(md_file)
        if content:
            all_data[md_file] = content

    # Make sure save directory exists
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Save all content to one JSON file
    json_path = os.path.join(SAVE_DIR, JSON_FILENAME)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f" All data saved to {json_path}")

if __name__ == "__main__":
    main()



