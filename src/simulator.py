import os
import time
import threading
import random
import requests
from datetime import datetime
from src.helpers.logger import get_logger
from src.helpers.settings import API_URL, SENSOR_MAPPINGS

logger = get_logger("simulator")

class SensorSimulator:
    def __init__(self):
        logger.info(f"Using API URL: {API_URL}")
        self.running = True
        self.sensor_types = {
            "temperature": {
                "range": (-10, 50),
                "unit": "°C",
                "critical_threshold": 45,
                "distribution": {
                    "normal": (15, 35),  # Normal operating range
                    "probability": 0.8    # 80% chance of normal values
                }
            },
            "humidity": {
                "range": (0, 100),
                "unit": "%",
                "critical_threshold": {"min": 20, "max": 75},
                "distribution": {
                    "normal": (30, 60),   # Comfortable range
                    "probability": 0.7    # 70% chance of comfortable values
                }
            },
            "traffic": {
                "range": (0, 500),
                "unit": "vehicles/hour",
                "critical_threshold": 350,
                "distribution": {
                    "normal": (100, 300), # Normal traffic range
                    "probability": 0.75   # 75% chance of normal traffic
                }
            },
            "air-quality": {
                "range": (0, 500),
                "unit": "AQI",
                "critical_threshold": 150,
                "distribution": {
                    "normal": (0, 100),   # Good to Moderate AQI
                    "probability": 0.85   # 85% chance of good air quality
                }
            }
        }

    def generate_sensor_data(self, sensor_type: str, sensor_id: str, location: str):
        """Generate sensor data based on type with realistic distributions"""
        config = self.sensor_types[sensor_type]
        min_val, max_val = config["range"]
        
        while self.running:
            # Use distribution settings for more realistic data
            if random.random() < config["distribution"]["probability"]:
                # Generate value within normal range
                normal_min, normal_max = config["distribution"]["normal"]
                value = random.uniform(normal_min, normal_max)
            else:
                # Generate value in full range, possibly critical
                value = random.uniform(min_val, max_val)
            
            self.send_sensor_data(sensor_type, sensor_id, location, value)
            time.sleep(5)

    def validate_location(self, sensor_type: str, sensor_id: str, location: str) -> str:
        """Validate and ensure correct location for sensor"""
        try:
            correct_location = SENSOR_MAPPINGS[sensor_type][sensor_id]
            if location != correct_location:
                logger.warning(f"Location mismatch for {sensor_id}. Expected: {correct_location}, Got: {location}")
            return correct_location
        except KeyError:
            logger.error(f"Invalid sensor configuration: type={sensor_type}, id={sensor_id}")
            raise ValueError(f"Invalid sensor configuration")

    def send_sensor_data(self, sensor_type: str, sensor_id: str, location: str, value: float):
        """Send sensor data with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Always use correct location from mapping
                correct_location = self.validate_location(sensor_type, sensor_id, location)
                
                data = {
                    "sensor_id": sensor_id,
                    "type": sensor_type,
                    "location": correct_location,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
                
                response = requests.post(
                    f"{API_URL}/api/publish",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=5  # Add timeout
                )
                
                if response.status_code == 200:
                    unit = self.sensor_types[sensor_type]["unit"]
                    status = self.get_status(sensor_type, value)
                    logger.info(f"Sent {sensor_type} data: {value}{unit} from {correct_location} [{status}]")
                    return
                else:
                    logger.warning(f"Failed to send data: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to send data after {max_retries} attempts")

    def get_status(self, sensor_type: str, value: float) -> str:
        """Determine if value is critical based on thresholds"""
        config = self.sensor_types[sensor_type]
        threshold = config["critical_threshold"]
        
        if isinstance(threshold, dict):  # For humidity with min/max
            return "critical" if value < threshold["min"] or value > threshold["max"] else "normal"
        else:  # For other sensors with single threshold
            return "critical" if value > threshold else "normal"

    def start(self):
        """Start all sensor simulators"""
        threads = []
        
        # Create sensors for each type using the mappings
        for sensor_type, mappings in SENSOR_MAPPINGS.items():
            for sensor_id, location in mappings.items():
                thread = threading.Thread(
                    target=self.generate_sensor_data,
                    args=(sensor_type, sensor_id, location)
                )
                thread.daemon = True
                threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        logger.info(f"Started {len(threads)} sensor simulators")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping sensor simulators...")
            self.running = False
            
            for thread in threads:
                thread.join(timeout=1)
            
            logger.info("Sensor simulators stopped")

def generate_sensor_value(sensor_type: str) -> float:
    """Generate random sensor values within realistic ranges"""
    ranges = {
        'temperature': {'min': 0, 'max': 45},    # Celsius
        'humidity': {'min': 10, 'max': 90},      # Percentage
        'air-quality': {'min': 0, 'max': 150},   # AQI
        'traffic': {'min': 0, 'max': 500}        # Vehicles per hour
    }
    
    range_values = ranges.get(sensor_type, {'min': 0, 'max': 100})
    return random.uniform(range_values['min'], range_values['max'])

if __name__ == "__main__":
    simulator = SensorSimulator()
    simulator.start()