from google import genai
from typing import Dict, Any, List
import json
from .config import settings
from .schemas import StructuredSummary, InterventionProposal
from .prompt_builder import build_gemini_prompt

def extract_json_from_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def generate_intervention(summary: StructuredSummary, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt = build_gemini_prompt(summary, evidence)
    
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        raise ValueError(f"Failed to initialize Gemini client: {e}")
        
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": InterventionProposal}
        )
        
        raw_text = response.text
        json_str = extract_json_from_markdown(raw_text)
        
        try:
            data = json.loads(json_str)
            proposal = InterventionProposal(**data)
            return proposal.model_dump()
        except Exception as e:
            # Retry with repair prompt
            repair_prompt = f"The previous output failed JSON validation. Fix it and return valid JSON only. Error: {str(e)}\n\nOriginal output:\n{json_str}"
            response2 = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=repair_prompt,
                config={"response_mime_type": "application/json", "response_schema": InterventionProposal}
            )
            raw_text2 = response2.text
            json_str2 = extract_json_from_markdown(raw_text2)
            data2 = json.loads(json_str2)
            proposal2 = InterventionProposal(**data2)
            return proposal2.model_dump()
            
    except Exception as e:
        raise ValueError(f"Failed to generate valid intervention proposal: {e}")
