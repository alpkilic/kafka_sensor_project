import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from kafka import KafkaProducer
from src.helpers.settings import (
    KAFKA_BOOTSTRAP_SERVERS, 
    KAFKA_TOPIC_DATA, 
    KAFKA_TOPIC_ALERTS, 
    PARTITION_MAPPING,
    THRESHOLDS,
    KAFKA_CONFIG
)
from src.helpers.logger import get_logger
from src.helpers.utils import get_unit, is_critical
from src import database

logger = get_logger("service")

class SensorService:
    """Service for handling sensor data operations"""
    def __init__(self):
        self.producer = None
        self.init_kafka()

    def init_kafka(self):
        """Initialize Kafka producer with retry logic"""
        max_retries = 30
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to Kafka (Attempt {attempt + 1}/{max_retries})")
                self.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                logger.info("Successfully connected to Kafka")
                return True
            except Exception as e:
                logger.warning(f"Failed to connect to Kafka: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Kafka after maximum retries")
                    return False

    def publish_data(self, data: Dict) -> Dict:
        """Publish sensor data to appropriate Kafka topic based on criticality"""
        if self.producer is None:
            if not self.init_kafka():
                return {"status": "error", "message": "Kafka connection failed"}
        
        is_critical_data = is_critical(data.get('type', ''), data.get('value', 0))
        
        try:
            if is_critical_data:
                # 🚨 CRITICAL DATA → sensor-alerts topic (2 partitions)
                location = data.get('location', '').encode('utf-8')
                future = self.producer.send(
                    topic=KAFKA_TOPIC_ALERTS,
                    value=data,
                    key=location  # Use location for partitioning across 2 partitions
                )
                record_metadata = future.get(timeout=10)
                
                logger.info(f"🚨 CRITICAL - Sent {data.get('type')} data to {KAFKA_TOPIC_ALERTS} partition {record_metadata.partition}")
                
                return {
                    "status": "success", 
                    "message": f"Critical data published to {KAFKA_TOPIC_ALERTS}",
                    "critical": True,
                    "topic": KAFKA_TOPIC_ALERTS,
                    "partition": record_metadata.partition
                }
                
            else:
                # ✅ NORMAL DATA → sensor-data topic (4 partitions by sensor type)
                sensor_type = data.get('type', '')
                partition = PARTITION_MAPPING.get(sensor_type, 0)
                future = self.producer.send(
                    topic=KAFKA_TOPIC_DATA,
                    value=data,
                    partition=partition
                )
                record_metadata = future.get(timeout=10)
                
                logger.info(f"✅ NORMAL - Sent {data.get('type')} data to {KAFKA_TOPIC_DATA} partition {record_metadata.partition}")
                
                return {
                    "status": "success", 
                    "message": f"Normal data published to {KAFKA_TOPIC_DATA}",
                    "critical": False,
                    "topic": KAFKA_TOPIC_DATA,
                    "partition": record_metadata.partition
                }
                
        except Exception as e:
            logger.error(f"Failed to publish to Kafka: {e}")
            return {
                "status": "error",
                "message": f"Failed to publish data: {str(e)}",
                "critical": is_critical_data
            }

    def create_notification(self, data: Dict) -> Dict:
        """Create notification payload for critical alert"""
        sensor_type = data.get('type', '')
        value = data.get('value', 0)
        location = data.get('location', '')
        
        alert_message = f"Critical {sensor_type} of {value}{get_unit(sensor_type)} detected at {location}"
        
        severity = "high"
        if sensor_type == "temperature":
            if value > 48 or value < -15:
                severity = "critical"
        elif sensor_type == "humidity":
            if value < 15 or value > 85:
                severity = "critical"
        elif sensor_type == "traffic":
            if value > 400:
                severity = "critical"
        elif sensor_type == "air-quality":
            if value > 200:
                severity = "critical"
        
        notification = {
            "sensor_id": data.get("sensor_id", ""),
            "type": sensor_type,
            "location": location,
            "value": value,
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "alert_message": alert_message,
            "severity": severity,
            "recipients": ["operations@example.com"]
        }
        
        logger.info(f"Notification prepared for {sensor_type} alert: {alert_message}")
        
        return notification

    def handle_email(self, alert_data):
        """Handle email alert creation"""
        data = alert_data.dict() if hasattr(alert_data, 'dict') else alert_data
        
        subject = f"CRITICAL ALERT: {data['type'].upper()} - {data['location']}"
        body = f"""
        Critical sensor reading detected!
        
        Sensor ID: {data['sensor_id']}
        Type: {data['type']}
        Location: {data['location']}
        Value: {data['value']}{get_unit(data['type'])}
        Timestamp: {data['timestamp']}
        
        Please take immediate action.
        """
        
        return {
            "sensor_id": data['sensor_id'],
            "type": data['type'],
            "location": data['location'],
            "value": data['value'],
            "timestamp": data['timestamp'],
            "subject": subject,
            "body": body.strip(),
            "to": ["alerts@example.com"],
            "cc": [],
            "priority": "high"
        }

    @staticmethod
    def get_analysis(sensor_type: Optional[str] = None, location: Optional[str] = None) -> Dict:
        """Get analysis data from database"""
        return database.get_analysis(sensor_type, location)

# Create global service instance
sensor_service = SensorService()