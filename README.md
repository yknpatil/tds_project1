# TDS Virtual TA - Discourse Responder

**Project:** TDS Virtual TA  
**Objective:** Create a virtual Teaching Assistant that responds to queries using TDS course content and Discourse discussions.

---

## Overview

This project builds a virtual TA capable of understanding and responding to student queries on the TDS Discourse forum. It leverages course material and past forum posts, processes the data through embeddings, and serves responses using a FastAPI backend.

---

## Project Workflow

### 1. Scrape Data

#### Course Content
- **URL:** [TDS Jan 2025 Course Site](https://tds.s-anand.net/#/2025-01/)
- **Script:** `1_scrape_course.py`
- **Method:** Scraped using markdown files
- **Output:** `3_all_course_data.json`

#### Discourse Posts
- **URL:** [TDS Discourse Forum](https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34)
- **Script:** `2_scrape_discourse.py`
- **Method:** Scraped from Discourse site
- **Output:** `4_discourse_posts_2025.json`

---

### 2. Embed Data with Jina AI

- **Script:** `5_embedding_768.py`
- **Course Embeddings:** `6_embedded_data_768.json`
- **Discourse Embeddings:** `7_embedded_discourse_768.json`

---

### 3. Upload to Supabase

- **Script:** `8_supabase_dataupload.py`
- **Note:** Supabase security level must be set to **"Public can view all rows"**

---

### 4. Backend API using FastAPI

- **Script:** `main.py`
- **Purpose:** Serve the virtual TA's responses using embedded data

---

### 5. Testing with Promptfoo

- **Config File:** `9.project-tds-virtual-ta-promptfoo_y.yaml`
- **Tool:** [Promptfoo](https://github.com/promptfoo/promptfoo)

---

### 6. Deployment

- **Platform:** GitHub + Render
- **Deployed Files:**
  - `requirements.txt`
  - `Dockerfile`
  - `LICENSE` (MIT)
  - All source scripts and data

---

## File Structure

| File | Description |
|------|-------------|
| `1_scrape_course.py` | Scrapes course content |
| `2_scrape_discourse.py` | Scrapes Discourse posts |
| `3_all_course_data.json` | Course data output |
| `4_discourse_posts_2025.json` | Discourse data output |
| `5_embedding_768.py` | Jina-based embedding |
| `6_embedded_data_768.json` | Embedded course content |
| `7_embedded_discourse_768.json` | Embedded forum content |
| `8_supabase_dataupload.py` | Uploads embeddings to Supabase |
| `main.py` | FastAPI app backend |
| `9.project-tds-virtual-ta-promptfoo_y.yaml` | Testing config |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container configuration |
| `LICENSE` | MIT license info |

---

## License
This project is licensed under the [MIT License](LICENSE).
