from typing import Any, Dict, List, Tuple
from .schemas import InterpretedField
from .field_catalog import CATALOG
import re

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    items: List[Tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # For lists, we don't fully flatten here to preserve the list structure
            # but we can return it as is or handle it specifically
            items.append((new_key, v))
        else:
            items.append((new_key, v))
    return dict(items)

def normalize_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, str):
        val_strip = val.strip()
        if val_strip == "sem informação":
            return None
        # Handle percentages
        if val_strip.endswith("%"):
            try:
                return float(val_strip.replace("%", "").replace(",", "."))
            except ValueError:
                pass
        # Handle numeric strings
        if re.match(r'^-?\d+(?:[.,]\d+)?$', val_strip):
            try:
                # If there is a comma and no dot, might be decimal comma
                if "," in val_strip and "." not in val_strip:
                    return float(val_strip.replace(",", "."))
                if "." in val_strip and "," not in val_strip:
                    return float(val_strip)
                return float(val_strip.replace(",", ""))
            except ValueError:
                pass
    return val

def interpret_fields(api_data: Dict[str, Any]) -> Tuple[List[InterpretedField], List[str], Dict[str, Any], List[Dict[str, Any]]]:
    interpreted_fields: List[InterpretedField] = []
    warnings: List[str] = []
    unmapped_fields: Dict[str, Any] = {}
    epi_records: List[Dict[str, Any]] = []

    # Detect epidemiological records (lists)
    for key, value in api_data.items():
        if isinstance(value, list):
            if key in ["parametros", "notificacoes", "casos", "records"]:
                epi_records.extend(value)

    flat_data = flatten_dict(api_data)

    for k, v in flat_data.items():
        # Only process scalar values or try to find matching keys for list items
        if isinstance(v, list) and not isinstance(v, dict):
            continue

        base_key = k.split('.')[-1].split('_')[-1] # Try to find exact match or partial
        
        # Simple heuristic: find if any catalog key is a substring or exact match
        matched_catalog_entry = None
        for cat_k, cat_v in CATALOG.items():
            if cat_k == k or cat_k in k:
                matched_catalog_entry = cat_v
                break

        if matched_catalog_entry:
            norm_val = normalize_value(v)
            interpreted = InterpretedField(
                field_name=k,
                group=matched_catalog_entry.group,
                raw_value=v,
                normalized_value=norm_val,
                priority=matched_catalog_entry.priority,
                interpretation=matched_catalog_entry.why_it_matters,
                planning_implication=matched_catalog_entry.how_it_guides_plan,
                dengue_relevance=matched_catalog_entry.dengue_relevance,
                is_direct_dengue_risk=matched_catalog_entry.is_direct_dengue_risk,
                requires_local_validation=matched_catalog_entry.requires_local_validation_when_missing and norm_val is None
            )
            interpreted_fields.append(interpreted)
            
            if matched_catalog_entry.priority in ["very_high", "high"] and norm_val is None:
                warnings.append(f"High priority field '{k}' is null or missing.")
            if matched_catalog_entry.requires_local_validation_when_missing and norm_val is None:
                warnings.append(f"Field '{k}' requires local validation because it is missing.")
        else:
            unmapped_fields[k] = v

    # Also process epi_records
    for record in epi_records:
        if isinstance(record, dict):
            for k, v in record.items():
                if k in CATALOG:
                    cat_v = CATALOG[k]
                    norm_val = normalize_value(v)
                    interpreted = InterpretedField(
                        field_name=k,
                        group=cat_v.group,
                        raw_value=v,
                        normalized_value=norm_val,
                        priority=cat_v.priority,
                        interpretation=cat_v.why_it_matters,
                        planning_implication=cat_v.how_it_guides_plan,
                        dengue_relevance=cat_v.dengue_relevance,
                        is_direct_dengue_risk=cat_v.is_direct_dengue_risk,
                        requires_local_validation=cat_v.requires_local_validation_when_missing and norm_val is None
                    )
                    interpreted_fields.append(interpreted)

    return interpreted_fields, warnings, unmapped_fields, epi_records
