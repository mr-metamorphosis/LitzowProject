import os
import pdfplumber
import pandas as pd
import logging

# Configure logging
LOG_FILE = "pdf_processing.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Folder containing PDF files
PDF_FOLDER = "/Users/amradityapradhan/Documents/Steve-Litzow/BulkDataDownload/BlockchainData"
OUTPUT_EXCEL = "ocr-AIData.xlsx"

def extract_text_from_pdf(pdf_path):
    """Extract text from a single PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                text += extracted_text + "\n" if extracted_text else ""
        logging.info(f"Successfully processed: {pdf_path}")
    except Exception as e:
        logging.error(f"Error processing {pdf_path}: {e}")
    return text.strip()

def process_pdfs_in_folder(folder_path):
    """Extract text from all PDFs in a folder and save it in a DataFrame."""
    data = []
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logging.warning("No PDF files found in the directory.")
    
    for filename in pdf_files:
        pdf_path = os.path.join(folder_path, filename)
        text = extract_text_from_pdf(pdf_path)
        data.append({"Filename": filename, "Extracted Text": text})
    
    logging.info(f"Processed {len(pdf_files)} PDF files.")
    return pd.DataFrame(data)

def save_to_excel(df, output_path):
    """Save the DataFrame to an Excel file."""
    try:
        df.to_excel(output_path, index=False)
        logging.info(f"Saved OCR output to {output_path}")
    except Exception as e:
        logging.error(f"Error saving to Excel: {e}")

if __name__ == "__main__":
    logging.info("PDF processing started.")
    df = process_pdfs_in_folder(PDF_FOLDER)
    if not df.empty:
        save_to_excel(df, OUTPUT_EXCEL)
    else:
        logging.warning("No text extracted from PDFs.")
    logging.info("PDF processing completed.")
