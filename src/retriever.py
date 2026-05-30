from typing import List, Dict, Any
from .vector_store import vector_store

def retrieve_evidence(queries: List[str], top_k_per_query: int = 3) -> List[Dict[str, Any]]:
    all_results = []
    seen_texts = set()
    
    for query in queries:
        results = vector_store.search(query, top_k=top_k_per_query)
        for res in results:
            if res["text"] not in seen_texts:
                seen_texts.add(res["text"])
                all_results.append(res)
                
    return all_results
