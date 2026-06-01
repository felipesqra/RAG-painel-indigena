from typing import Dict, Any, List
from .schemas import StructuredSummary, InterpretedField, Period

def analyze_structured_data(api_data: Dict[str, Any], interpreted_fields: List[InterpretedField], dsei: str, data_init: str, data_end: str) -> StructuredSummary:
    summary = StructuredSummary(
        dsei=dsei,
        period=Period(data_init=data_init, data_end=data_end)
    )
    if "casos_dengue" in api_data or "casos_dengue_mensal" in api_data:
        summary.dengue_cases = {
            "total": api_data.get("casos_dengue", 0),
            "monthly": api_data.get("casos_dengue_mensal", []),
            "data_init": api_data.get("data_init", data_init),
            "data_end": api_data.get("data_end", data_end),
        }

    for field in interpreted_fields:
        if "governance" in field.group.lower() or field.dengue_relevance == "governance":
            summary.governance_indicators.append(field)
            if field.requires_local_validation:
                summary.missing_information.append(field)
        
        elif "water supply" in field.group.lower():
            summary.water_supply_indicators.append(field)
        
        elif "solid waste" in field.group.lower():
            summary.solid_waste_indicators.append(field)
            if field.is_direct_dengue_risk:
                summary.direct_dengue_risk_factors.append(field)
            else:
                summary.important_public_health_issues_not_direct_dengue_risk.append(field)
        
        elif "sewage" in field.group.lower() or "sanitation" in field.group.lower():
            summary.sanitation_indicators.append(field)
            summary.important_public_health_issues_not_direct_dengue_risk.append(field)
            
        elif field.dengue_relevance == "clinical":
            if "Warning signs" in field.group or "Severe signs" in field.group or "Hospitalization" in field.group:
                summary.clinical_severity_indicators.append(field)
            else:
                summary.epidemiological_indicators.append(field)

        # Catch-all for other risk factors
        if field.is_direct_dengue_risk and field not in summary.direct_dengue_risk_factors:
            summary.direct_dengue_risk_factors.append(field)

        if field.requires_local_validation and field not in summary.missing_information:
            summary.missing_information.append(field)

    # Build recommended retrieval queries
    queries = set()
    queries.add(f"dengue {dsei}")
    queries.add(f"saúde indígena {dsei}")
    if summary.direct_dengue_risk_factors:
        queries.add("recipientes artificiais dengue")
    if summary.water_supply_indicators:
        queries.add("armazenamento de água dengue")
    if summary.solid_waste_indicators:
        queries.add("resíduos sólidos dengue")
    if summary.clinical_severity_indicators:
        queries.add("dengue sinais de alarme severa")

    summary.recommended_retrieval_queries = list(queries)

    return summary
