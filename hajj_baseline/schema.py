"""Input and output rules shared by the M4 baseline."""
from __future__ import annotations
from copy import deepcopy
import math

DOMAIN_FIELDS = {
    "crowd": {"density_people_per_m2": "number", "queue_minutes": "number", "distance_km": "number"},
    "health": {"fatigue_1_to_5": "number", "stress_1_to_5": "number", "emergency_event": "boolean"},
    "environment": {"temperature_c": "number"},
}
FIELD_PATHS = tuple(f"{d}.{name}" for d,fs in DOMAIN_FIELDS.items() for name in fs)
QUALITY = {"observed", "missing", "stale", "noisy", "conflicting"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}
ACTIONS = {"LOW": "ROUTINE_MONITORING", "MEDIUM": "PRIORITY_HUMAN_REVIEW", "HIGH": "URGENT_HUMAN_REVIEW"}


class ContractError(ValueError):
    pass


def validate_case(case: dict) -> dict:
    if not isinstance(case, dict) or not isinstance(case.get("case_id"), str) or not case["case_id"].strip():
        raise ContractError("case_id must be a non-empty string.")
    if case.get("data_origin") != "illustrative_synthetic":
        raise ContractError("Only illustrative synthetic cases are included in M4.")
    domains = case.get("domains")
    if not isinstance(domains, dict):
        raise ContractError("domains must be an object.")
    for domain, names in DOMAIN_FIELDS.items():
        if not isinstance(domains.get(domain), dict):
            raise ContractError(f"Missing domain: {domain}")
        for name, kind in names.items():
            field = domains[domain].get(name)
            if not isinstance(field, dict) or field.get("quality") not in QUALITY:
                raise ContractError(f"Invalid observation: {domain}.{name}")
            value = field.get("value")
            if field["quality"] == "missing":
                if value is not None:
                    raise ContractError(f"{domain}.{name} must be null when missing")
            elif kind == "boolean":
                if not isinstance(value, bool):
                    raise ContractError(f"{domain}.{name} must be boolean")
            elif isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
                raise ContractError(f"{domain}.{name} must be a finite number")
            if not isinstance(field.get("source"), str) or not field["source"].strip():
                raise ContractError(f"{domain}.{name} needs a source")
            if field["quality"] == "conflicting":
                alternates=field.get("alternate_values")
                if not isinstance(alternates,list) or not alternates:
                    raise ContractError(f"{domain}.{name} needs conflicting source values")
                for alt in alternates:
                    if not isinstance(alt,dict) or not isinstance(alt.get("source"),str) or not alt["source"]:
                        raise ContractError(f"{domain}.{name} needs valid alternate sources")
                    a=alt.get("value")
                    if kind=="boolean":
                        if not isinstance(a,bool):
                            raise ContractError("Invalid alternate boolean")
                    elif isinstance(a,bool) or not isinstance(a,(int,float)) or not math.isfinite(a):
                        raise ContractError("Invalid alternate number")
            age=field.get("age_minutes")
            if age is not None and (isinstance(age,bool) or not isinstance(age,(int,float)) or not math.isfinite(age) or age<0):
                raise ContractError(f"Invalid age: {domain}.{name}")
    return deepcopy(case)


def quality_alerts(case: dict) -> list[str]:
    return [f"{d}.{f}: {case['domains'][d][f]['quality']}"
            for d,names in DOMAIN_FIELDS.items() for f in names
            if case["domains"][d][f]["quality"] != "observed"]


def validate_decision(result: dict, case: dict) -> dict:
    if not isinstance(result, dict) or result.get("case_id") != case["case_id"]:
        raise ContractError("Invalid decision or case ID.")
    if result.get("status") not in {"DECISION", "ABSTAIN"}:
        raise ContractError("Invalid decision status.")
    if not isinstance(result.get("summary"), str) or not result["summary"].strip():
        raise ContractError("Decision needs an explanation.")
    for name in ("evidence_used", "uncertainty_flags", "verify_fields"):
        if not isinstance(result.get(name), list) or not all(isinstance(x,str) for x in result[name]):
            raise ContractError(f"{name} must be a string array")
    for name in ("evidence_used","verify_fields"):
        if set(result[name])-set(FIELD_PATHS):
            raise ContractError(f"Unknown fields in {name}")
    for path in result["evidence_used"]:
        d,f=path.split(".")
        if case["domains"][d][f]["quality"]!="observed":
            raise ContractError("Cannot cite missing or unreliable evidence.")
    if result["status"]=="DECISION":
        risk=result.get("risk_level")
        if risk not in RISK_LEVELS or result.get("recommended_action")!=ACTIONS[risk]:
            raise ContractError("Invalid risk/action pair.")
        if not result["evidence_used"] or result["verify_fields"]:
            raise ContractError("Decision needs evidence and no verification request.")
    else:
        if result.get("risk_level") is not None or result.get("recommended_action")!="REQUEST_VERIFICATION":
            raise ContractError("Invalid abstention.")
        if not result["verify_fields"]:
            raise ContractError("Abstention must identify fields to check.")
        if not any(case["domains"][d][f]["quality"]!="observed" for d,f in (p.split(".") for p in result["verify_fields"])):
            raise ContractError("Cannot claim observed fields are missing.")
    if any(x.lower().strip() in {"short readable issue","issue","none"} for x in result["uncertainty_flags"]):
        raise ContractError("Placeholder uncertainty flag.")
    return {
        "case_id":result["case_id"],"status":result["status"],
        "risk_level":result.get("risk_level"),
        "recommended_action":result["recommended_action"],
        "evidence_used":list(dict.fromkeys(result["evidence_used"])),
        "uncertainty_flags":result["uncertainty_flags"],
        "verify_fields":list(dict.fromkeys(result["verify_fields"])),
        "summary":result["summary"].strip()[:1500],
    }


def safe_abstention(case: dict, reason: str) -> dict:
    fields=[p for p in FIELD_PATHS if case["domains"][p.split(".")[0]][p.split(".")[1]]["quality"]!="observed"]
    if not fields:
        fields=list(FIELD_PATHS)
    return {
        "case_id":case["case_id"],"status":"ABSTAIN","risk_level":None,
        "recommended_action":"REQUEST_VERIFICATION","evidence_used":[],
        "uncertainty_flags":["model_response_invalid"],
        "verify_fields":fields,
        "summary":"The model response did not pass the output checks. Human review is required.",
    }
