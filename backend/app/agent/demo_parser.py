"""
ResQ-AI Deterministic Demo Mode Natural Language Incident Parser.
"""

import re
from app.agent.llm_service import IncidentData

WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twelve": 12,
    "fifteen": 15,
}


def parse(text: str) -> IncidentData:
    """Deterministically extracts structured IncidentData from natural-language emergency reports."""
    raw = str(text or "").strip()
    lower = raw.lower()

    # 1. Extract Node / Location (e.g. N1..N8, H1..H2, A1..A3, University, Downtown)
    node_match = re.search(r"\b(N[1-8]|H[12]|A[1-3])\b", raw, re.IGNORECASE)
    if node_match:
        location = node_match.group(1).upper()
    elif "university" in lower:
        location = "University"
    elif "downtown" in lower:
        location = "N1"
    else:
        location = "N1"

    # 2. Extract Victim Count (avoid matching N1..N8 node numbers)
    cleaned_for_nums = re.sub(r"\b[NHA][1-9]\b", "", raw, flags=re.IGNORECASE)
    cleaned_for_nums = re.sub(r"alert\(\d+\)", "", cleaned_for_nums, flags=re.IGNORECASE)
    num_match = re.search(r"\b(\d+)\b", cleaned_for_nums)
    victim_count = 5
    if num_match:
        victim_count = int(num_match.group(1))
    else:
        for word, val in WORD_NUMBERS.items():
            if re.search(rf"\b{word}\b", lower):
                victim_count = val
                break

    # 3. Extract Weather
    if "heavy rain" in lower or "torrential" in lower or "storm" in lower:
        weather = "Heavy Rain"
    elif "rain" in lower:
        weather = "Rain"
    elif "fog" in lower:
        weather = "Fog"
    elif "snow" in lower:
        weather = "Snow"
    else:
        weather = "Clear"

    # 4. Extract Road Blockage / Condition
    road_blocked = any(w in lower for w in ("blocked", "closed", "impassable", "bridge cut", "bridges cut"))
    if road_blocked:
        road_condition = "Blocked"
    elif "flood" in lower:
        road_condition = "Flooded"
    elif "wet" in lower or "rain" in lower:
        road_condition = "Wet"
    else:
        road_condition = "Clear"

    # 5. Extract Incident Type
    if "fire" in lower:
        inc_type = "Fire"
        inc_code = "fire"
    elif "flood" in lower:
        inc_type = "Flood"
        inc_code = "flood"
    elif any(w in lower for w in ("crash", "pileup", "collision", "accident", "highway")):
        inc_type = "Road Accident"
        inc_code = "road_accident"
    else:
        inc_type = "Medical Emergency"
        inc_code = "medical_emergency"

    # 6. Extract Severity
    if any(w in lower for w in ("severe", "massive", "catastrophic", "critical", "pileup")) or victim_count >= 5:
        severity = "high"
    elif victim_count >= 3:
        severity = "medium"
    else:
        severity = "low"

    return IncidentData(
        type=inc_type,
        incident_type=inc_code,
        severity=severity,
        victim_count=victim_count,
        location=location,
        weather=weather,
        road_condition=road_condition,
        road_blocked=road_blocked,
    )
