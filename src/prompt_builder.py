from typing import Dict, Any, List
from .schemas import StructuredSummary

def build_gemini_prompt(summary: StructuredSummary, evidence: List[Dict[str, Any]]) -> str:
    prompt = f"""
You are an assistant for decision support in Indigenous public health.

Generate a dengue intervention proposal in Portuguese for the requested DSEI.

Use exclusively:
1. Structured data returned by the API.
2. Deterministic field interpretations supplied by the system.
3. Structured summary produced by the analyzer.
4. Technical evidence retrieved from PDF documents.
5. Explicit system rules.

Do not invent information.
Do not invent local facts.
Do not invent village names.
Do not invent epidemiological values.
Do not invent responsible actors.
Do not claim fieldwork occurred.
Do not claim an action already exists unless it appears in structured data.
Do not use PDF evidence as if it were local data.
Use PDF evidence only as technical support.

Do not treat all sanitation problems as direct dengue risks.
For dengue, prioritize conditions related to:
* artificial containers;
* uncovered water storage;
* irregular waste collection;
* discarded materials that can accumulate water;
* unsafe domestic storage when water supply is absent or irregular.

When a sanitation issue is important but not directly dengue-specific, classify it separately.

When responsibility is unknown, recommend local validation before assigning actions.

When the community already performs an action, avoid accusatory language and propose feasible support.

The output must be valid JSON only.
Do not return Markdown.
Do not wrap the JSON in code fences.
The proposal must be in Portuguese.

The JSON must match exactly the InterventionProposal schema.

Data context:
DSEI: {summary.dsei}
Period: {summary.period.data_init} to {summary.period.data_end}

Dengue Case Context:
{summary.dengue_cases}

Direct Dengue Risk Factors:
{[f.model_dump() for f in summary.direct_dengue_risk_factors]}

Important Health Issues (Not Direct Dengue Risk):
{[f.model_dump() for f in summary.important_public_health_issues_not_direct_dengue_risk]}

Missing Information / Needs Validation:
{[f.model_dump() for f in summary.missing_information]}

Governance Indicators:
{[f.model_dump() for f in summary.governance_indicators]}

Epidemiological / Clinical Indicators:
{[f.model_dump() for f in summary.epidemiological_indicators + summary.clinical_severity_indicators]}

Technical Evidence from RAG:
"""
    for ev in evidence:
        prompt += f"- Document: {ev['document']}, Page: {ev['page']}\n  Text: {ev['text']}\n\n"
        
    return prompt
