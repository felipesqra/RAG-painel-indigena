from typing import List, Dict, Any
import re

def chunk_text(pages_data: List[Dict[str, Any]], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    chunks = []
    
    for page in pages_data:
        text = page["text"]
        if not text:
            continue
            
        # Very simple tokenization by words
        words = re.findall(r'\S+', text)
        
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "chunk_id": f"{page['filename']}_p{page['page']}_{i}",
                "filename": page["filename"],
                "page": page["page"],
                "text": chunk_text
            })
            
            i += (chunk_size - overlap)
            
    return chunks
