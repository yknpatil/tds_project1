from supabase import create_client, Client
import json
import os

url = "https://cbhembzupxtksglokupq.supabase.co"
key = ""  #key to be added
supabase: Client = create_client(url, key)

base_path = "/mnt/c/Users/user/Documents/TDS_Project1"

# Upload discourse_768 data
with open(os.path.join(base_path, "embedded_discourse_768.json"), "r") as f:
    discourse_data = json.load(f)

for filename, item in discourse_data.items():
    record = {
        "source_name": filename,
        "content": item["content_html"],
        "embedding": item["embedding"],
    }
    try:
        response = supabase.table("discourse_768").upsert(record, on_conflict="source_name").execute()
        print(f"[discourse_768] Inserted/Updated {filename}")
    except Exception as e:
        print(f"[discourse_768] Error inserting {filename}: {e}")

# Upload courseinfo_768 data
with open(os.path.join(base_path, "embedded_data_768.json"), "r") as f:
    course_data = json.load(f)

for filename, item in course_data.items():
    record = {
        "source_name": filename,
        "content": item["content"],
        "embedding": item["embedding"],
    }
    try:
        response = supabase.table("courseinfo_768").upsert(record, on_conflict="source_name").execute()
        print(f"[courseinfo_768] Inserted/Updated {filename}")
    except Exception as e:
        print(f"[courseinfo_768] Error inserting {filename}: {e}")

print(" All uploads completed.")



