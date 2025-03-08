import requests
import time
import os
import csv
import fitz  # PyMuPDF for PDF text extraction
from datetime import datetime, timedelta

# Base API URL and API Key
BASE_URL = "https://api.regulations.gov/v4"
API_KEY = "4MMLaxc6RObTFzeEoCyJt7VOGH7SzX5Qe8D9WzFd"

# Headers for API requests
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# --- User Input Section ---
print("Select a category:")
print("  1. Artificial Intelligence")
print("  2. Blockchain")
print("  3. Crypto Currency")
category_choice = input("Enter 1, 2, or 3: ").strip()

if category_choice == "1":
    SEARCH_KEYWORDS = [
        "algorithmic transparency", 
        "bias mitigation",
        "autonomous systems",
        "machine learning"
    ]
elif category_choice == "2":
    SEARCH_KEYWORDS = [
        "distributed ledger"
        #"smart contracts", 
        #"virtual assets", 
        #"stablecoins", 
        #"DeFi"
    ]
elif category_choice == "3":
    SEARCH_KEYWORDS = [
        #"virtual currency", 
        "digital assets", 
        #"tokenization", 
        #"AML/CFT", 
        #"exchanges"
    ]
else:
    custom_keywords = input("Enter your custom search keywords (comma-separated): ")
    SEARCH_KEYWORDS = [kw.strip() for kw in custom_keywords.split(",")]

folder_name = input("Enter folder name to save documents (default: regulations_pdfs): ").strip()
if not folder_name:
    folder_name = "regulations_pdfs"

# Define local directories for saving data
SAVE_DIR = folder_name
os.makedirs(SAVE_DIR, exist_ok=True)
CSV_FILE = os.path.join(SAVE_DIR, "regulations_data.csv")

# --- Additional Filters ---
# Filter by document type (for "rules" and "proposed rules")
# Depending on the API, you may need to adjust the exact values.
DOCUMENT_TYPE_FILTER = "Proposed Rule,Rule"
# Filter by posted date (documents from the past 3 years)
start_date = (datetime.utcnow() - timedelta(days=3 * 365)).strftime("%Y-%m-%dT%H:%M:%SZ")

# Log configuration
print("\nConfiguration:")
print(f"  Search Keywords: {SEARCH_KEYWORDS}")
print(f"  Document Types: {DOCUMENT_TYPE_FILTER}")
print(f"  Posted Date From: {start_date}")
print(f"  Save Folder: {SAVE_DIR}\n")

# --- Functions ---

def handle_rate_limits(response):
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        print(f"Rate limit hit! Sleeping for {retry_after} seconds...")
        time.sleep(retry_after)
        return True
    return False

def get_documents():
    documents = []
    page = 1
    three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")

    while len(documents) < 1000:
        params = {
            "filter[searchTerm]": " OR ".join(SEARCH_KEYWORDS),
            "filter[postedDate][ge]": three_years_ago,
            "filter[documentType]": DOCUMENT_TYPE_FILTER,
            "page[size]": 100,
            "page[number]": page
        }
        print(f"Fetching page {page}...")
        response = requests.get(f"{BASE_URL}/documents", headers=HEADERS, params=params)
        if handle_rate_limits(response):
            continue
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}: {response.status_code}")
            print("Error details:", response.text)
            break
        data = response.json()
        items = data.get("data", [])
        if not items:
            print("No more documents found.")
            break
        documents.extend(items)
        print(f"Retrieved {len(items)} documents from page {page}")
        page += 1
    return documents[:1000]

def get_attachments(doc_id):
    attach_url = f"{BASE_URL}/documents/{doc_id}/attachments"
    response = requests.get(attach_url, headers=HEADERS)
    if handle_rate_limits(response):
        return None
    if response.status_code != 200:
        print(f"Failed to fetch attachments for {doc_id}")
        return None
    attachments = response.json().get("data", [])
    file_urls = []
    for attachment in attachments:
        file_formats = attachment.get("attributes", {}).get("fileFormats", [])
        if not isinstance(file_formats, list):
            continue
        for file_format in file_formats:
            if "fileUrl" in file_format:
                file_urls.append(file_format["fileUrl"])
    return file_urls if file_urls else None

def download_pdf(doc_id, file_url, count):
    file_path = os.path.join(SAVE_DIR, f"{doc_id}_{count}.pdf")
    response = requests.get(file_url)
    if handle_rate_limits(response):
        return None
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded PDF: {file_path}")
        return file_path
    else:
        print(f"Failed to download PDF for {doc_id}")
        return None

def extract_text_from_pdf(pdf_path):
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

def save_to_csv(documents):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["document_id", "title", "docket_id", "abstract", "document_text"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for doc in documents:
            doc_id = doc.get("id")
            title = doc.get("attributes", {}).get("title", "Unknown")
            docket_id = doc.get("attributes", {}).get("docketId", "Unknown")
            abstract = doc.get("attributes", {}).get("abstract", "No abstract available")
            file_urls = get_attachments(doc_id)
            document_texts = []
            if file_urls:
                for count, file_url in enumerate(file_urls, start=1):
                    pdf_path = download_pdf(doc_id, file_url, count)
                    if pdf_path:
                        text = extract_text_from_pdf(pdf_path)
                        if text:
                            document_texts.append(text)
            document_text = "\n\n".join(document_texts) if document_texts else "No PDFs available"
            writer.writerow({
                "document_id": doc_id,
                "title": title,
                "docket_id": docket_id,
                "abstract": abstract,
                "document_text": document_text
            })
            print(f"Saved document {doc_id} to CSV")

# --- Main Execution ---
documents = get_documents()
if documents:
    save_to_csv(documents)
else:
    print("No documents retrieved.")
