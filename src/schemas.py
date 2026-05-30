from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Any, Dict, List, Optional, Union

class InterventionRequest(BaseModel):
    dsei: str
    data_init: date
    data_end: date
    use_mock: bool = False

    def model_post_init(self, __context: Any) -> None:
        if self.data_end < self.data_init:
            raise ValueError("data_end cannot be earlier than data_init")

class RawAPIResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

class FieldInterpretation(BaseModel):
    field_name: str
    group: str
    priority: str # "very_high" | "high" | "medium_high" | "medium" | "low"
    why_it_matters: str
    how_it_guides_plan: str
    dengue_relevance: str # "direct" | "indirect" | "vulnerability" | "governance" | "data_quality" | "clinical" | "not_direct"
    is_direct_dengue_risk: bool
    is_governance_field: bool
    requires_local_validation_when_missing: bool = False
    recommended_action_logic: str = ""

class InterpretedField(BaseModel):
    field_name: str
    group: str
    raw_value: Any
    normalized_value: Any
    priority: str
    interpretation: str
    planning_implication: str
    dengue_relevance: str
    is_direct_dengue_risk: bool
    requires_local_validation: bool

class Period(BaseModel):
    data_init: str
    data_end: str

class StructuredSummary(BaseModel):
    dsei: str
    period: Period
    dengue_cases: Any = []
    territorial_context: List[InterpretedField] = []
    water_supply_indicators: List[InterpretedField] = []
    solid_waste_indicators: List[InterpretedField] = []
    sanitation_indicators: List[InterpretedField] = []
    epidemiological_indicators: List[InterpretedField] = []
    clinical_severity_indicators: List[InterpretedField] = []
    governance_indicators: List[InterpretedField] = []
    direct_dengue_risk_factors: List[InterpretedField] = []
    important_public_health_issues_not_direct_dengue_risk: List[InterpretedField] = []
    missing_information: List[InterpretedField] = []
    data_quality_warnings: List[str] = []
    recommended_retrieval_queries: List[str] = []

class Evidence(BaseModel):
    document: str
    page: str
    evidence_summary: str
    how_it_supports_the_intervention: str

class ActionItem(BaseModel):
    action: str
    justification: str
    responsible_actor: str
    supporting_actors: List[str] = []
    validation_needed: bool = False

class Responsibility(BaseModel):
    action: str
    main_responsible: str
    supporters: List[str] = []
    basis_in_data: str = ""
    observation: str = ""

class LocalIndicators(BaseModel):
    dengue: List[str] = []
    water_supply: List[str] = []
    solid_waste: List[str] = []
    sanitation: List[str] = []
    governance: List[str] = []
    missing_information: List[str] = []

class DengueRiskInterpretation(BaseModel):
    directly_related_to_dengue: List[str] = []
    important_sanitation_problems_but_not_direct_dengue_risk: List[str] = []
    insufficient_information_requiring_local_validation: List[str] = []

class InterventionProposal(BaseModel):
    title: str
    situation_summary: str
    local_indicators: LocalIndicators
    dengue_risk_interpretation: DengueRiskInterpretation
    technical_evidence: List[Evidence] = []
    general_objective: str
    immediate_actions_0_7_days: List[ActionItem] = []
    short_term_actions_30_days: List[ActionItem] = []
    medium_term_actions_90_days: List[ActionItem] = []
    suggested_responsibilities: List[Responsibility] = []
    monitoring_indicators: List[str] = []
    data_limitations: List[str] = []
    executive_summary: str
