def calculate_risk(factors: dict) -> dict:
    p_delay_given_rain = 0.8
    p_delay_given_no_rain = 0.2
    
    p_high_sev_given_high_victims = 0.9
    p_high_sev_given_low_victims = 0.3
    
    p_hosp_overload_given_multi = 0.7
    p_hosp_overload_given_single = 0.1
    
    is_rain = factors.get("heavy_rain", False)
    victims = factors.get("victim_count", 0)
    is_multi = factors.get("multiple_incidents", False)
    
    p_delay = p_delay_given_rain if is_rain else p_delay_given_no_rain
    p_high_sev = p_high_sev_given_high_victims if victims > 5 else p_high_sev_given_low_victims
    p_overload = p_hosp_overload_given_multi if is_multi else p_hosp_overload_given_single
    
    overall_risk = (p_delay + p_high_sev + p_overload) / 3.0
    
    return {
        "travel_delay_probability": p_delay,
        "high_severity_probability": p_high_sev,
        "hospital_overload_probability": p_overload,
        "overall_risk": min(overall_risk, 1.0),
        "note": "ALL probabilities are simulated/educational."
    }
