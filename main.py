from fastapi import FastAPI, Depends, HTTPException, Header
from typing import Optional, Dict, Any
from src.schemas import InterventionRequest
from src.config import settings
from src.mock_client import get_mock_data
from src.api_client import fetch_api_data
from src.field_interpreter import interpret_fields
from src.structured_data_analyzer import analyze_structured_data
from src.retriever import retrieve_evidence
from src.intervention_generator import generate_intervention
from src.pdf_loader import load_all_pdfs
from src.chunker import chunk_text
from src.vector_store import vector_store

app = FastAPI(title="Dengue Intervention Proposal API")

@app.on_event("startup")
async def startup_event():
    if settings.REINDEX_ON_STARTUP:
        print("Reindexing on startup...")
        pages = load_all_pdfs(settings.PDF_DIR)
        if pages:
            chunks = chunk_text(pages)
            vector_store.index_chunks(chunks)

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health_check():
    pdf_count = 0
    import os
    if os.path.exists(settings.PDF_DIR):
        pdf_count = len([f for f in os.listdir(settings.PDF_DIR) if f.lower().endswith(".pdf")])
        
    return {
        "status": "ok",
        "rag_index_ready": vector_store.collection.count() > 0 if vector_store.collection else False,
        "pdf_count": pdf_count,
        "mock_api": settings.MOCK_API
    }

@app.post("/admin/reindex")
def reindex_pdfs(dependencies=Depends(verify_token)):
    pages = load_all_pdfs(settings.PDF_DIR)
    if not pages:
        return {
            "status": "success",
            "message": "No PDFs found to index",
            "pdf_count": 0,
            "chunk_count": 0
        }
        
    chunks = chunk_text(pages)
    vector_store.index_chunks(chunks)
    
    import os
    pdf_count = len([f for f in os.listdir(settings.PDF_DIR) if f.lower().endswith(".pdf")])
    
    return {
        "status": "success",
        "message": "Index rebuilt successfully",
        "pdf_count": pdf_count,
        "chunk_count": len(chunks)
    }

@app.post("/generate-intervention")
async def create_intervention(request: InterventionRequest):
    use_mock = request.use_mock or settings.MOCK_API
    
    # 1. Fetch data
    if use_mock:
        source = "mock_api"
        api_data = get_mock_data()
    else:
        source = "real_api"
        api_data = await fetch_api_data(request.dsei, request.data_init.isoformat(), request.data_end.isoformat())
        
    if "error" in api_data:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {api_data['error']}")
        
    # 2. Interpret fields
    interpreted_fields, warnings, unmapped, epi_records = interpret_fields(api_data)
    
    # 3. Analyze structured data
    summary = analyze_structured_data(
        api_data, 
        interpreted_fields, 
        request.dsei, 
        request.data_init.isoformat(), 
        request.data_end.isoformat()
    )
    
    # 4. Retrieve evidence
    queries = summary.recommended_retrieval_queries
    evidence = retrieve_evidence(queries)
    
    if not evidence:
        warnings.append("Não foram recuperadas evidências documentais suficientes. A proposta foi gerada com base nos dados estruturados e deve ser validada tecnicamente.")
        
    # 5. Generate proposal
    try:
        proposal = generate_intervention(summary, evidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # 6. Return response
    return {
        "dsei": request.dsei,
        "data_init": request.data_init.isoformat(),
        "data_end": request.data_end.isoformat(),
        "source": source,
        "api_data": api_data,
        "interpreted_fields": [f.model_dump() for f in interpreted_fields],
        "structured_summary": summary.model_dump(),
        "retrieved_evidence": evidence,
        "intervention_proposal": proposal,
        "warnings": warnings
    }
