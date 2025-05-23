from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from src.helpers.utils import is_critical

class SensorType(str, Enum):
    """Enum for sensor types"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    TRAFFIC = "traffic" 
    AIR_QUALITY = "air-quality"

class SensorData(BaseModel):
    """Base model for sensor data"""
    sensor_id: str
    type: str  # Using string instead of enum for simplicity
    location: str
    value: float
    timestamp: Optional[str] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)
    
    def is_critical(self) -> bool:
        """Check if the sensor data is in critical range"""
        return is_critical(self.type, self.value)

class NotificationPayload(BaseModel):
    """Structure for notification endpoint"""
    sensor_id: str
    type: str
    location: str
    value: float
    timestamp: str
    alert_message: str
    severity: str
    recipients: List[str] = ["operations@example.com"]

class EmailPayload(BaseModel):
    """Structure for email endpoint"""
    sensor_id: str
    type: str
    location: str
    value: float
    timestamp: str
    subject: str
    body: str
    to: List[str] = ["alerts@example.com"]
    cc: List[str] = []
    priority: str = "high"

class AnalysisResponse(BaseModel):
    """Response structure for analysis endpoint"""
    sensor_type: Optional[str] = None
    location: Optional[str] = None
    data_points: int
    time_range: Dict[str, str]
    average_value: float
    max_value: float
    min_value: float
    critical_events: int
    trend: str
    insights: List[str]