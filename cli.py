import argparse
import asyncio
import json
import os
from datetime import datetime
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

async def main():
    parser = argparse.ArgumentParser(description="Dengue Intervention Proposal CLI")
    parser.add_argument("--dsei", type=str, help="DSEI name")
    parser.add_argument("--data-init", type=str, help="Start date YYYY-MM-DD")
    parser.add_argument("--data-end", type=str, help="End date YYYY-MM-DD")
    parser.add_argument("--mock", action="store_true", help="Use mock API")
    parser.add_argument("--reindex", action="store_true", help="Rebuild RAG index")
    parser.add_argument("--output", type=str, help="Save output JSON to file")
    
    args = parser.parse_args()
    
    if args.reindex:
        print("Rebuilding RAG index...")
        pages = load_all_pdfs(settings.PDF_DIR)
        if pages:
            chunks = chunk_text(pages)
            vector_store.index_chunks(chunks)
            print(f"Index rebuilt successfully. Indexed {len(chunks)} chunks.")
        else:
            print("No PDFs found to index.")
        return

    if not args.dsei or not args.data_init or not args.data_end:
        print("Error: --dsei, --data-init, and --data-end are required when not using --reindex")
        return
        
    try:
        # Validate dates
        datetime.strptime(args.data_init, "%Y-%m-%d")
        datetime.strptime(args.data_end, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format")
        return

    use_mock = args.mock or settings.MOCK_API
    
    if use_mock:
        print("Using mock API...")
        source = "mock_api"
        api_data = get_mock_data()
    else:
        print("Fetching data from real API...")
        source = "real_api"
        api_data = await fetch_api_data(args.dsei, args.data_init, args.data_end)
        
    if "error" in api_data:
        print(f"Error fetching data: {api_data['error']}")
        return
        
    print("Interpreting fields...")
    interpreted_fields, warnings, unmapped, epi_records = interpret_fields(api_data)
    
    print("Analyzing structured data...")
    summary = analyze_structured_data(
        api_data, 
        interpreted_fields, 
        args.dsei, 
        args.data_init, 
        args.data_end
    )
    
    print("Retrieving evidence...")
    queries = summary.recommended_retrieval_queries
    evidence = retrieve_evidence(queries)
    
    if not evidence:
        warnings.append("Não foram recuperadas evidências documentais suficientes. A proposta foi gerada com base nos dados estruturados e deve ser validada tecnicamente.")
        
    print("Generating intervention proposal...")
    try:
        proposal = generate_intervention(summary, evidence)
    except Exception as e:
        print(f"Error generating proposal: {e}")
        return
        
    response = {
        "dsei": args.dsei,
        "data_init": args.data_init,
        "data_end": args.data_end,
        "source": source,
        "api_data": api_data,
        "interpreted_fields": [f.model_dump() for f in interpreted_fields],
        "structured_summary": summary.model_dump(),
        "retrieved_evidence": evidence,
        "intervention_proposal": proposal,
        "warnings": warnings
    }
    
    print("\n--- Intervention Proposal Generated ---\n")
    print(json.dumps(proposal, indent=2, ensure_ascii=False))
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        print(f"\nFull response saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
