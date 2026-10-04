"""
ResQ-AI Bayesian Risk Engine (FAI Module VIII - Uncertainty).

Implements a 7-variable conditional probability model for emergency response risk:
Variables:
1. Weather
2. Road Condition
3. Traffic
4. Travel Delay
5. Victim Severity
6. Hospital Capacity / Overload
7. Composite Response Risk

All probabilities are explicitly labeled as simulated/educational.
"""

from typing import Any, Dict, List


DISCLAIMER = "Educational simulation — not for real-world emergency dispatch. All probabilities are simulated/educational."


class BayesianRiskEngine:
    """Bayesian conditional probability risk calculator for emergency dispatch."""

    def calculate(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        return calculate_risk(factors)


def calculate_risk(factors: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes conditional probabilities P(delay | weather, road),
    P(high_severity | victims, severity), P(hospital_overload | victims, multi_incident),
    and composite response risk.
    """
    if not isinstance(factors, dict):
        factors = {}

    weather_raw = str(factors.get("weather", "Clear")).lower()
    road_raw = str(factors.get("road_condition", factors.get("roadCondition", "Clear"))).lower()
    sev_raw = str(factors.get("severity", "Medium")).lower()
    victims = int(factors.get("victim_count", factors.get("victims", 0)) or 0)

    is_heavy_rain = bool(
        factors.get("heavy_rain", False)
        or "rain" in weather_raw
        or "storm" in weather_raw
        or "flood" in weather_raw
        or "snow" in weather_raw
    )
    is_fog = "fog" in weather_raw
    is_blocked_or_flooded = bool(
        factors.get("road_blocked", False)
        or "block" in road_raw
        or "flood" in road_raw
        or "icy" in road_raw
        or "closed" in road_raw
    )
    is_wet = "wet" in road_raw or "congested" in road_raw
    is_multi = bool(factors.get("multiple_incidents", False) or victims >= 8)

    # 1. Weather Risk Prior P(WeatherRisk)
    if is_heavy_rain:
        weather_risk = 0.80
    elif is_fog:
        weather_risk = 0.55
    else:
        weather_risk = 0.15

    # 2. Traffic & Road Condition Risk P(Traffic | Weather, RoadCondition)
    if is_blocked_or_flooded and is_heavy_rain:
        traffic_risk = 0.88
        road_risk = 0.90
    elif is_blocked_or_flooded:
        traffic_risk = 0.75
        road_risk = 0.80
    elif is_heavy_rain or is_wet:
        traffic_risk = 0.65
        road_risk = 0.55
    else:
        traffic_risk = 0.20
        road_risk = 0.15

    # 3. Travel Delay Conditional Probability P(Delay | Weather, RoadCondition, Traffic)
    if is_heavy_rain and is_blocked_or_flooded:
        p_delay = 0.88
    elif is_heavy_rain:
        p_delay = 0.80
    elif is_blocked_or_flooded:
        p_delay = 0.72
    elif is_wet or is_fog:
        p_delay = 0.45
    else:
        p_delay = 0.20

    # 4. High Severity Conditional Probability P(HighSeverity | VictimCount, ReportedSeverity)
    if "critical" in sev_raw or victims >= 8:
        p_high_sev = 0.92
    elif "high" in sev_raw or victims > 5:
        p_high_sev = 0.90
    elif "medium" in sev_raw or victims >= 3:
        p_high_sev = 0.45
    else:
        p_high_sev = 0.30

    # 5. Hospital Overload Conditional Probability P(HospitalOverload | MultipleIncidents, VictimCount)
    if is_multi or victims >= 10:
        p_overload = 0.75 if victims >= 10 else 0.70
    elif victims >= 6:
        p_overload = 0.45
    else:
        p_overload = 0.10

    # 6. Composite Risk Score (0.0 to 1.0)
    overall_risk = round((p_delay + p_high_sev + p_overload) / 3.0, 4)
    overall_risk = min(max(overall_risk, 0.0), 1.0)

    if overall_risk >= 0.75:
        risk_level = "CRITICAL"
    elif overall_risk >= 0.50:
        risk_level = "HIGH"
    elif overall_risk >= 0.30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    factors_chart: List[Dict[str, Any]] = [
        {"name": "Weather", "risk": round(weather_risk * 100)},
        {"name": "Traffic", "risk": round(traffic_risk * 100)},
        {"name": "Travel Delay", "risk": round(p_delay * 100)},
        {"name": "Victim Severity", "risk": round(p_high_sev * 100)},
        {"name": "Hospital Load", "risk": round(p_overload * 100)},
        {"name": "Road Cond.", "risk": round(road_risk * 100)},
    ]

    return {
        "travel_delay_probability": p_delay,
        "high_severity_probability": p_high_sev,
        "hospital_overload_probability": p_overload,
        "weather_risk": weather_risk,
        "traffic_risk": traffic_risk,
        "road_condition_risk": road_risk,
        "overall_risk": overall_risk,
        "composite_risk_score": overall_risk,
        "composite_risk": overall_risk,
        "risk_score": round(overall_risk * 100, 1),
        "risk_level": risk_level,
        "factors": factors_chart,
        "conditional_probabilities": {
            "P(delay | weather, road)": p_delay,
            "P(high_severity | victim_count)": p_high_sev,
            "P(hospital_overload | incidents)": p_overload,
        },
        "note": "ALL probabilities are simulated/educational.",
        "disclaimer": DISCLAIMER,
    }
