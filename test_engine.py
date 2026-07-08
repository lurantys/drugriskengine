import pytest
from app import RISK_RULES

def match_alerts(conditions, medications):
    alerts = []
    for cond_code, cond_display in conditions:
        for rule in RISK_RULES:
            if cond_code != rule["condition_code"]:
                continue
            for med_code, med_display in medications:
                if med_code != rule["rxnorm"]:
                    continue
                alerts.append({
                    "condition": cond_display,
                    "condition_code": cond_code,
                    "medication": med_display,
                    "rxnorm": med_code,
                    "severity": rule["severity"],
                    "justification": rule["justification"]
                })
    return alerts

def test_pregnancy_ibuprofen_critical():
    conds = {("77386006", "Pregnancy")}
    meds = {("5640", "Ibuprofen")}
    alerts = match_alerts(conds, meds)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "CRITICAL"
    assert "fetal" in alerts[0]["justification"].lower()

def test_asthma_propranolol_critical():
    conds = {("195967001", "Asthma")}
    meds = {("8745", "Propranolol")}
    alerts = match_alerts(conds, meds)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "CRITICAL"
    assert "bronchoconstriction" in alerts[0]["justification"]

def test_ckd_spironolactone_high():
    conds = {("723190009", "Chronic Kidney Disease")}
    meds = {("114488", "Spironolactone")}
    alerts = match_alerts(conds, meds)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "HIGH"
    assert "hyperkalemia" in alerts[0]["justification"]

def test_diabetes_pseudoephedrine_medium():
    conds = {("73211009", "Diabetes")}
    meds = {("8896", "Pseudoephedrine")}
    alerts = match_alerts(conds, meds)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "MEDIUM"
    assert "blood glucose" in alerts[0]["justification"]

def test_heart_failure_ibuprofen_high():
    conds = {("84114007", "Heart Failure")}
    meds = {("5640", "Ibuprofen")}
    alerts = match_alerts(conds, meds)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "HIGH"
    assert "fluid retention" in alerts[0]["justification"]

def test_no_match_returns_empty():
    conds = {("73211009", "Diabetes")}
    meds = {("5640", "Ibuprofen")}
    alerts = match_alerts(conds, meds)
    assert len(alerts) == 0

def test_multiple_alerts_same_patient():
    conds = {("77386006", "Pregnancy"), ("84114007", "Heart Failure")}
    meds = {("5640", "Ibuprofen")}
    alerts = match_alerts(conds, meds)
    assert len(alerts) == 2
    severities = [a["severity"] for a in alerts]
    assert "CRITICAL" in severities
    assert "HIGH" in severities

def test_severity_values():
    severities = {r["severity"] for r in RISK_RULES}
    assert severities == {"CRITICAL", "HIGH", "MEDIUM"}
