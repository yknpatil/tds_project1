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
- **Method:** Scraped from Discourse API
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

* **Script:** `main.py`
* **Purpose:** This FastAPI application acts as the central brain for the Virtual Teaching Assistant (TA). It takes your questions and gives back clear, relevant answers from various knowledge sources.

**How the Search Works (Search Logic):**

Our API uses a smart **Retrieval-Augmented Generation (RAG)** system to get you the best answer. It prioritizes information like this:

1.  **Direct URL First:**
    * When you ask a question, the API first checks if you've given it a specific **Discourse forum link** (like in the `url` field).
    * If you have, it will **focus on fetching and searching for content directly from that exact Discourse thread**. This helps ensure the answer is super relevant to what you're looking at.

2.  **Vector Database Fallback:**
    * If you didn't provide a URL, or if the content from the URL wasn't enough to answer your question, the system then **switches to searching its powerful vector database**.
    * Your question (and any image you included) is turned into **numerical embeddings** using **Jina AI's models**.
    * These embeddings are then used to find similar information in our **Supabase vector database**. This database holds pre-processed content from **both the official TDS course materials** (like `tds.s-anand.net` pages) **and the Discourse forum posts**. So, if no direct URL was given, it searches both.

3.  **Answer Generation:**
    * The most relevant information found (either from the direct URL or the vector database) is then given to a **Large Language Model (LLM)**. Currently, we use `openai/gpt-4o-mini` through `aipipe.org/openrouter`. The LLM uses this information to create a clear and concise answer.

    * **Example Answer Format:**
        ```json
        {
          "answer": "You must use `gpt-3.5-turbo-0125`, even if the AI Proxy only supports `gpt-4o-mini`. Use the OpenAI API directly for this question.",
          "links": [
            {
              "url": "[https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/4](https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/4)",
              "text": "Use the model that’s mentioned in the question."
            },
            {
              "url": "[https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/3](https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/3)",
              "text": "My understanding is that you just have to use a tokenizer, similar to what Prof. Anand used, to get the number of tokens and multiply that by the given rate."
            }
          ]
        }
        ```

4.  **No Answer Found:**
    * If, even after checking both the direct URL and the entire vector database, the system can't find enough confident information to answer your question, it will simply reply with: "**I don't know**."

This multi-step search ensures the TA provides the most accurate and helpful response possible.

---

### 5. Testing with Promptfoo

- **Config File:** `9.project-tds-virtual-ta-promptfoo_y.yaml`
- **Tool:** [Promptfoo](https://github.com/promptfoo/promptfoo)
- **Configuration** Configured the llm-rubric assertions to leverage an AI proxy token and the gpt-4o-mini model

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
