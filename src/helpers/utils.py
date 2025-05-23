from typing import Dict
from datetime import datetime
from src.helpers.settings import THRESHOLDS

def get_level(value: float, ranges: Dict[float, str]) -> str:
    """Get level based on value and predefined ranges"""
    for threshold, level in sorted(ranges.items()):
        if value <= threshold:
            return level
    return list(ranges.values())[-1]

def get_comfort_level(temperature: float) -> str:
    """Calculate comfort level based on temperature"""
    ranges = {
        0: "freezing",
        10: "very cold",
        18: "cold",
        24: "comfortable",
        30: "warm",
        40: "hot"
    }
    return get_level(temperature, ranges)

def get_humidity_level(humidity):
    """Calculate comfort level based on humidity"""
    if humidity < 20:
        return "very dry"
    elif humidity < 30:
        return "dry"
    elif humidity < 60:
        return "comfortable"
    elif humidity < 80:
        return "humid"
    else:
        return "very humid"

def get_traffic_level(traffic):
    """Calculate traffic congestion level with updated thresholds"""
    if traffic < 50:
        return "free flowing"
    elif traffic < 150:
        return "light"
    elif traffic < 250:
        return "moderate"
    elif traffic < 350:
        return "heavy"
    else:
        return "critical"

def get_air_quality_level(aqi):
    """Calculate air quality health impact"""
    if aqi < 50:
        return "good"
    elif aqi < 100:
        return "moderate"
    elif aqi < 150:
        return "unhealthy for sensitive groups"
    elif aqi < 200:
        return "unhealthy"
    elif aqi < 300:
        return "very unhealthy"
    else:
        return "hazardous"

def is_critical(sensor_type: str, value: float) -> bool:
    """Check if sensor reading is critical - FIXED VERSION"""
    threshold = THRESHOLDS.get(sensor_type, {})
    min_val = threshold.get("min", 0)
    max_val = threshold.get("max", float('inf'))
    
    # TÜM SENSOR TİPLERİ İÇİN AYNI LOGİC
    is_below_min = value < min_val
    is_above_max = value > max_val
    
    return is_below_min or is_above_max

def get_unit(sensor_type: str) -> str:
    """Get unit for sensor type"""
    return {
        "temperature": "°C",
        "humidity": "%",
        "traffic": "vehicles/hour",
        "air-quality": "AQI"
    }.get(sensor_type, "")