import pandas as pd

file_path = "/Users/amradityapradhan/Documents/Steve-Litzow/BulkDataDownload/OCR_data/ocr-CryptoData-again.xlsx"
df = pd.read_excel(file_path)

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += max(chunk_size - overlap, 1)
    return chunks

chunked_data = []

# Process each document (each row) separately
for idx, row in df.iterrows():
    doc_id = row['Filename']         
    text = row['Extracted Text']     # The text to be chunked
    
    if not isinstance(text, str) or not text.strip():
        continue
    
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    
    for chunk in chunks:
        chunked_data.append({
            'Filename': doc_id,
            'Chunk': chunk
        })

# list to a DataFrame for easier export
chunked_df = pd.DataFrame(chunked_data)

chunked_df.to_csv("chunked_cryptodata.csv", index=False)

print("Chunking complete. Here are a few sample chunks:")
print(chunked_df.head())
