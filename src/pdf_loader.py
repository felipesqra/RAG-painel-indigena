import fitz  # PyMuPDF
import pdfplumber
import os
from typing import List, Dict, Any

def extract_text_from_pdf(filepath: str) -> List[Dict[str, Any]]:
    pages_data = []
    filename = os.path.basename(filepath)
    try:
        # Try PyMuPDF first
        doc = fitz.open(filepath)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            if not text.strip():
                # Fallback to pdfplumber if PyMuPDF yields empty string
                try:
                    with pdfplumber.open(filepath) as pdf:
                        if page_num < len(pdf.pages):
                            p = pdf.pages[page_num]
                            text = p.extract_text() or ""
                except Exception:
                    pass
            
            # Simple OCR fallback or just empty text if nothing works
            pages_data.append({
                "filename": filename,
                "page": page_num + 1,
                "text": text.strip()
            })
        doc.close()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return pages_data

def load_all_pdfs(directory: str) -> List[Dict[str, Any]]:
    all_pages = []
    if not os.path.exists(directory):
        return all_pages
        
    for filename in os.listdir(directory):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(directory, filename)
            all_pages.extend(extract_text_from_pdf(filepath))
            
    return all_pages
