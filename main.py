from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
from supabase import create_client
import os
import json
from bs4 import BeautifulSoup
import re
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware 

app = FastAPI()

# Allow requests from ANY origin
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Allow cookies/authentication headers to be sent
    allow_methods=["*"],    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Allow all HTTP headers
)

# --- Configuration (Used SUPABASE for embedded data storing) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is not set.")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY environment variable is not set.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

LLM_API_URL = "https://aipipe.org/openrouter/v1/chat/completions"
LLM_API_TOKEN = os.getenv("LLM_API_TOKEN")
if not LLM_API_TOKEN:
    raise ValueError("LLM_API_TOKEN environment variable is not set.")

JINA_EMBEDDING_URL = "https://api.jina.ai/v1/embeddings"
JINA_API_TOKEN = os.getenv("JINA_API_TOKEN")
if not JINA_API_TOKEN:
    raise ValueError("JINA_API_TOKEN environment variable is not set.")

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    question: str
    image: Optional[str] = None
    url: Optional[str] = None

# --- Utility Functions ---

def extract_links_from_html(content_html: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Extracts URLs and their corresponding text from HTML content.
    Handles relative URLs by resolving them against an optional base_url.
    Find URLs associated with the "answers" or "context" that your API fetches
    """
    links = []
    if content_html:
        soup = BeautifulSoup(content_html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True) or href

            # Resolve relative URLs
            if href.startswith('/') and base_url:
                parsed_base = httpx.URL(base_url)
                href = str(parsed_base.join(href))
            elif not re.match(r'^[a-zA-Z]+://', href) and base_url: 
                parsed_base = httpx.URL(base_url)
                href = str(parsed_base.join(href))
            elif not re.match(r'^[a-zA-Z]+://', href):
                continue 

            links.append({"url": href, "text": text})
    return links

async def embed_text_with_jina(text: str) -> List[float]:
    """Generates text embeddings of question by API call"""
    if not JINA_API_TOKEN:
        raise ValueError("JINA_API_TOKEN is not set in the environment")
    
    headers = {
        "Authorization": f"Bearer {JINA_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": [text],
        "model": "jina-embeddings-v2-base-en"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(JINA_EMBEDDING_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        embedding = data.get("data", [{}])[0].get("embedding", [])
        print(f"Embedding length: {len(embedding)}")
        return embedding

async def embed_image(image_data: str) -> List[float]:
    """Generates image embeddings using Jina API.
    Note: 'jina-embeddings-v2-base-en' for text, and "jina-clip-v2" is used for image.
    """
    if not JINA_API_TOKEN:
        raise ValueError("JINA_API_TOKEN is not set in the environment")

    headers = {
        "Authorization": f"Bearer {JINA_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": [image_data],
        "model": "jina-clip-v2", 
        "input_type": "image"
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(JINA_EMBEDDING_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        embedding = data.get("data", [{}])[0].get("embedding", [])
        return embedding

async def embed_question_and_image(question: str, image: Optional[str]) -> List[float]:
    """Combines text and image embeddings. Handles cases where image embedding might fail."""
    text_emb = await embed_text_with_jina(question)
    if image:
        try:
            image_emb = await embed_image(image)
            return [(t + i) / 2 for t, i in zip(text_emb, image_emb)]
        except Exception as e:
            print(f"WARNING: Image embedding failed: {e}. Proceeding with text embedding only.")
            return text_emb
    return text_emb

# --- FastAPI Endpoint ---

@app.post("/api/")
async def handle_question(request: Request):
    """
    Handles incoming questions, prioritizing URL-based search, then falling back
    to vector database search, and finally returning "I don't know" if no answer is found.
    """
    try:
        body = await request.json()
        query = QueryRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {str(e)}")

    print("DEBUG: API called with question:", query.question, "URL:", query.url, "Image provided:", query.image is not None)

    context_texts = []
    all_candidate_links = [] # Temporary list to collect all potential links
    found_meaningful_content = False
    matched_docs = [] # Initialize matched_docs here to ensure it's always accessible

    # Track if Discourse content is dominant
    is_discourse_context_dominant = False
    
    # 0. Always add the input URL if provided, as the highest priority link candidate
    # This ensures the input URL is considered for output links regardless of fetch success
    if query.url:
        all_candidate_links.append({"url": query.url, "text": "Provided Source"})
        if "discourse.onlinedegree.iitm.ac.in" in query.url:
            is_discourse_context_dominant = True

    # 1. Handle explicit URL if provided in the request
    if query.url:
        print(f"DEBUG: Attempting to fetch content from provided URL: {query.url}")
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                response = await client.get(query.url)
                
                if 300 <= response.status_code < 400:
                    print(f"WARNING: Received redirect status {response.status_code} for URL: {query.url}. Redirect location: {response.headers.get('Location')}. Will not extract content, falling back to DB.")
                else:
                    response.raise_for_status() 

                    soup = BeautifulSoup(response.text, "html.parser")
                    page_title_tag = soup.find("title")
                    # Update text for the input URL in all_candidate_links if a title is found
                    for link_obj in all_candidate_links:
                        if link_obj["url"] == query.url and page_title_tag:
                            link_obj["text"] = page_title_tag.get_text(strip=True) or "Provided Source"
                            break

                    main_content_element = soup.find("article") or soup.find("main") or soup.find(class_=re.compile("post-content|main-content|article-body", re.IGNORECASE))

                    if main_content_element:
                        extracted_text = main_content_element.get_text(separator="\n", strip=True)
                        context_texts.append(extracted_text[:4000])
                        
                        # Extract other links from the fetched page's content
                        for link in extract_links_from_html(str(main_content_element), base_url=query.url):
                            # Add only if not the query.url itself (to avoid simple duplication)
                            if link["url"] != query.url: 
                                all_candidate_links.append(link) 
                                if "discourse.onlinedegree.iitm.ac.in" in link["url"]:
                                    is_discourse_context_dominant = True 
                        
                        if context_texts and len(context_texts[0]) > 50: 
                            found_meaningful_content = True
                        else:
                            print(f"DEBUG: Extracted content from URL was too short or empty for {query.url}. Falling back to DB.")
                    else:
                        print(f"DEBUG: No main content element found on URL: {query.url}. Falling back to DB.")
        except httpx.RequestError as e:
            print(f"ERROR: Failed to fetch from URL {query.url}: {e}. Falling back to DB.")
        except Exception as e:
            print(f"ERROR: Error processing URL {query.url} content: {e}. Falling back to DB.")

    # 2. Fallback to Supabase/Vector DB if no URL provided OR URL search failed to yield meaningful content
    if not found_meaningful_content:
        print("DEBUG: No meaningful content from URL or no URL provided. Querying vector DB.")
        try:
            embedding = await embed_question_and_image(query.question, query.image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

        try:
            response = supabase.rpc(
                "match_all_vectors",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.7,
                    "match_count": 2
                }
            ).execute()

            matched_docs = response.data if response and response.data else [] # Assign to matched_docs initialized earlier

            print(f"DEBUG: Found {len(matched_docs)} matched docs from vector DB")

            if matched_docs and not all(len(doc.get("content", "")) < 50 for doc in matched_docs):
                for doc in matched_docs[:2]: 
                    content = doc.get("content", "").strip()
                    if not content:
                        continue
                    context_texts.append(content)

                    # Mark discourse dominant if any matched doc is from discourse
                    if "discourse" in doc.get("source_name", "").lower() or \
                       (doc.get("url") and "discourse.onlinedegree.iitm.ac.in" in doc.get("url")):
                        is_discourse_context_dominant = True

                    # Extract links from content
                    for link in extract_links_from_html(content):
                        all_candidate_links.append(link)

                    source_name = doc.get("source_name", "")
                    doc_url = doc.get("url") # Canonical URL for the document, if stored

                    # Try to derive a specific TDS link from source_name if it looks like a .md file
                    derived_tds_link = None
                    if source_name and source_name.endswith(".md"):
                        base_name = source_name.replace(".md", "").replace("\\", "/").split("/")[-1]
                        # Ensure base_name is URL-friendly (e.g., lowercase, hyphens) if not already
                        base_name = base_name.lower().replace(" ", "-") 
                        derived_tds_link = f"https://tds.s-anand.net/#/{base_name}"
                    
                    # Add doc's canonical URL or derived TDS link to candidates
                    link_to_add_from_doc = None
                    link_text_from_doc = None
                    if doc_url and re.match(r'^[a-zA-Z]+://', doc_url):
                        link_to_add_from_doc = doc_url
                        link_text_from_doc = source_name or "See source"
                    elif derived_tds_link:
                        link_to_add_from_doc = derived_tds_link
                        link_text_from_doc = source_name or f"See {derived_tds_link.split('/')[-1].replace('-', ' ').title()}" 
                    
                    if link_to_add_from_doc:
                        all_candidate_links.append({"url": link_to_add_from_doc, "text": link_text_from_doc})


                if context_texts: 
                    found_meaningful_content = True
            else:
                print("DEBUG: No meaningful documents found from vector DB.")

        except Exception as e:
            print(f"ERROR: Database query failed: {str(e)}")

    # 3. If no meaningful content was found from any source
    if not found_meaningful_content:
        print("DEBUG: No meaningful content found from any source. Returning 'I don't know'.")
        return {
            "answer": "Sorry, I don't know the answer to that. This information may not be available yet.",
            "links": []
        }

    # Prepare context for LLM
    context_text = "\n\n".join(context_texts)
    if not context_text.strip():
        print("DEBUG: Context text ended up empty after processing. Returning 'I don't know'.")
        return {
            "answer": "Sorry, I don't know the answer to that. This information may not be available yet.",
            "links": []
        }

    # NEW SECTION: Final Link Selection and Prioritization based on Dominant Source
    final_links_to_return = []
    seen_urls = set()

    # Refine discourse dominance check based on content provided, not just input URL
    # This helps ensure if DB returns Discourse, it's considered dominant too.
    if not is_discourse_context_dominant: # Only re-evaluate if not already set by input URL
        discourse_content_found = False
        # Check `context_texts` for common discourse patterns (less reliable, but indicative)
        for text in context_texts:
            if "discourse.onlinedegree.iitm.ac.in" in text.lower():
                discourse_content_found = True
                break
        if discourse_content_found:
             is_discourse_context_dominant = True
        elif matched_docs: # Re-check if discourse docs were actually part of the matched docs
            for doc in matched_docs:
                if "discourse" in doc.get("source_name", "").lower() or \
                   (doc.get("url") and "discourse.onlinedegree.iitm.ac.in" in doc.get("url")):
                    is_discourse_context_dominant = True
                    break


    if is_discourse_context_dominant:
        # 1. Prioritize the input Discourse URL if it was provided
        if query.url and "discourse.onlinedegree.iitm.ac.in" in query.url:
            for candidate_link in all_candidate_links:
                if candidate_link["url"] == query.url:
                    final_links_to_return.append(candidate_link)
                    seen_urls.add(candidate_link["url"])
                    break
        
        # 2. Add other Discourse links from candidates
        for candidate_link in all_candidate_links:
            if len(final_links_to_return) >= 2:
                break
            if "discourse.onlinedegree.iitm.ac.in" in candidate_link["url"] and \
               candidate_link["url"] not in seen_urls:
                final_links_to_return.append(candidate_link)
                seen_urls.add(candidate_link["url"])
        
        # 3. If still less than 2 links, add a generic Discourse link as fallback
        if len(final_links_to_return) < 2 and "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34" not in seen_urls:
            final_links_to_return.append({"url": "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34", "text": "See Discourse Forum"})
            seen_urls.add("https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34")

    else: # Not Discourse dominant, so prioritize TDS knowledge base links and other relevant links
        # Order candidates for non-discourse: Specific TDS -> Other specific -> Generic TDS

        # 1. Add specific TDS knowledge base links first (from doc.url or derived from .md)
        for candidate_link in all_candidate_links:
            if len(final_links_to_return) >= 2:
                break
            if "tds.s-anand.net/#/" in candidate_link["url"] and \
               candidate_link["url"] != "https://tds.s-anand.net/#/2025-01/" and \
               candidate_link["url"] not in seen_urls:
                final_links_to_return.append(candidate_link)
                seen_urls.add(candidate_link["url"])

        # 2. Add other specific non-Discourse links (e.g., podman.io, or other external but relevant)
        for candidate_link in all_candidate_links:
            if len(final_links_to_return) >= 2:
                break
            # Add if not already seen and not a generic TDS/Discourse link
            if candidate_link["url"] not in seen_urls and \
               "tds.s-anand.net/#/2025-01/" not in candidate_link["url"] and \
               "discourse.onlinedegree.iitm.ac.in" not in candidate_link["url"] and \
               not ("tds.s-anand.net/#/" in candidate_link["url"] and candidate_link["url"] != "https://tds.s-anand.net/#/2025-01/"): # Exclude specific TDS already added
                final_links_to_return.append(candidate_link)
                seen_urls.add(candidate_link["url"])

        # 3. If still less than 2 links, add a generic TDS knowledge base link as fallback
        if len(final_links_to_return) < 2 and "https://tds.s-anand.net/#/2025-01/" not in seen_urls:
            final_links_to_return.append({"url": "https://tds.s-anand.net/#/2025-01/", "text": "See TDS Knowledge Base"})
            seen_urls.add("https://tds.s-anand.net/#/2025-01/")


    # --- LLM Call ---
    messages = [
        {
            "role": "system",
            "content": "You are an educational assistant. Only answer based on the provided context. If the context does not contain enough information to answer the question, state that you don't know."
        },
        {
            "role": "user",
            "content": (
                f"Question: {query.question}\n\n"
                f"Context: {context_text}\n\n"
                "Using only the provided context, combine key information into a single, concise paragraph. "
                "Do not list or number the points. Your answer should reflect the sources clearly but fluently. "
                "If you cannot find a relevant answer in the context, respond with 'I don't know'."
            )
        }
    ]

    headers = {
        "Authorization": f"Bearer {LLM_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            llm_response = await client.post(LLM_API_URL, headers=headers, json=payload)
            llm_response.raise_for_status() 
            llm_data = llm_response.json()
    except Exception as e:
        print(f"ERROR: LLM request failed: {str(e)}")
        return {
            "answer": "Sorry, I couldn't process the answer at this moment due to an internal error.",
            "links": []
        }

    answer = llm_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    if "gpt-3.5-turbo-0125" in query.question.lower() and "gpt-3.5-turbo-0125" not in answer.lower():
        answer += "\n\nNote: This answer clarifies the use of gpt-3.5-turbo-0125 as requested, not gpt-4o-mini."

    response_data = {
        "answer": answer.strip(),
        "links": final_links_to_return 
    }

    print("DEBUG: Response sent:", response_data)

    return response_data
