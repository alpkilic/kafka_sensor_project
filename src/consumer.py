import json
import time
import threading
import requests
from typing import Dict, Any, Optional
from kafka import KafkaConsumer
from src.helpers.settings import (
    KAFKA_BOOTSTRAP_SERVERS, 
    KAFKA_TOPIC_DATA, 
    KAFKA_TOPIC_ALERTS,
    API_URL
)
from src.helpers.logger import get_logger
from src import database

logger = get_logger("consumer")

class BaseConsumer:
    """Base consumer class with common functionality"""
    def __init__(self, topic: str, group_id: str, consumer_id: Optional[int] = None):
        self.topic = topic
        self.group_id = group_id
        self.consumer_id = consumer_id
        self.consumer = None
        self.running = True

    def _create_consumer(self) -> Optional[KafkaConsumer]:
        """Create Kafka consumer with retry logic"""
        max_retries = 30
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Consumer {self.group_id}-{self.consumer_id} connecting...")
                consumer = KafkaConsumer(
                    self.topic,
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    group_id=self.group_id,
                    client_id=f"{self.group_id}-{self.consumer_id}",
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000
                )
                logger.info(f"✅ Consumer {self.group_id}-{self.consumer_id} connected!")
                return consumer
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def process_message(self, message: Dict[str, Any]) -> None:
        """Process individual message - to be implemented by subclasses"""
        raise NotImplementedError

    def run(self):
        """Main consumer loop with proper consumer initialization"""
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries and self.running:
            try:
                # Initialize consumer first
                self.consumer = self._create_consumer()
                if not self.consumer:
                    raise Exception(f"Failed to create consumer for {self.group_id}-{self.consumer_id}")

                logger.info(f"Consumer {self.group_id}-{self.consumer_id} starting message loop")
                
                while self.running:
                    try:
                        messages = self.consumer.poll(timeout_ms=1000)
                        if messages:
                            for tp, records in messages.items():
                                for record in records:
                                    if record.value:
                                        # Pass both message and partition info
                                        self.process_message(record.value, record.partition)
                        self.consumer.commit()
                    except Exception as e:
                        logger.error(f"Error processing messages: {e}")
                        time.sleep(1)
                        
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying consumer initialization ({retry_count}/{max_retries})...")
                    time.sleep(5)
                
            finally:
                if self.consumer:
                    try:
                        self.consumer.close()
                        logger.info(f"Consumer {self.group_id}-{self.consumer_id} closed")
                    except Exception as e:
                        logger.error(f"Error closing consumer: {e}")

class DataConsumer(BaseConsumer):
    """Consumer for processing sensor data"""
    def process_message(self, message: Dict[str, Any], partition: int = None):
        try:
            # Get assigned partitions safely
            partitions = []
            if self.consumer and self.consumer.assignment():
                partitions = [tp.partition for tp in self.consumer.assignment()]
            
            # Use the partition from the record itself
            current_partition = partition
            
            logger.info(f"""
            ╔══════════ DATA-CONSUMER-{self.consumer_id} ══════════╗
            ║ CONSUMER INFO:
            ║ 🆔 Consumer ID: {self.consumer_id}
            ║ 📊 Group ID: {self.group_id}
            ║ 🔄 All Partitions: {partitions}
            ║ 📍 Message From Partition: {current_partition}
            ║
            ║ MESSAGE DETAILS:
            ║ 📝 Type: {message.get('type', '').upper()}
            ║ 📍 Location: {message.get('location', '')}
            ║ 🔍 Sensor: {message.get('sensor_id', '')}
            ║ 📊 Value: {message.get('value', 0)}
            ║ 
            ║ PARTITION MAPPING:
            ║ 🌡️  Temperature → Partition 0
            ║ 💧 Humidity → Partition 1  
            ║ 🚗 Traffic → Partition 2
            ║ 🌫️  Air-Quality → Partition 3
            ╚═════════════════════════════════════╝
            """)
            
            # Process data first to check if critical
            processed_data = database.process_sensor_data(message)
            
            # Store raw and processed data
            database.store_raw_data(message)
            database.store_processed_data(processed_data)
            
            logger.info(f"[DATA-CONSUMER-{self.consumer_id}] Successfully processed {message.get('type')} data from {message.get('location')}")
            
        except Exception as e:
            logger.error(f"[DATA-CONSUMER-{self.consumer_id}] Error processing message: {e}")

class AlertConsumer(BaseConsumer):
    """Consumer for processing alerts"""
    def __init__(self, topic: str, group_id: str, alert_type: str, endpoint: str, consumer_id: Optional[int] = None):
        # Call parent constructor FIRST
        super().__init__(topic, group_id, consumer_id)
        # Then set additional attributes
        self.alert_type = alert_type
        self.endpoint = endpoint

    def process_message(self, message: Dict[str, Any], partition: int = None):
        try:
            # Get assigned partitions safely
            partitions = []
            if self.consumer and self.consumer.assignment():
                partitions = [tp.partition for tp in self.consumer.assignment()]
            
            logger.info(f"""
            ╔══════════ ALERT-CONSUMER-{self.consumer_id} ══════════╗
            ║ CONSUMER INFO:
            ║ 🆔 Consumer ID: {self.consumer_id}
            ║ 📊 Group ID: {self.group_id}
            ║ 🔄 Partitions: {partitions}
            ║ 📍 Message From Partition: {partition}
            ║ 🔔 Type: {self.alert_type.upper()}
            ║ 🔗 Endpoint: {self.endpoint}
            ║
            ║ ALERT DETAILS:
            ║ 📝 Type: {message.get('type', '').upper()}
            ║ 📍 Location: {message.get('location', '')}
            ║ 🔍 Sensor: {message.get('sensor_id', '')}
            ║ 📊 Value: {message.get('value', 0)}
            ╚═════════════════════════════════════╝
            """)
            
            # Forward to notification endpoints with retry logic
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f"{API_URL}/api/{self.endpoint}",
                        json=message,
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"[ALERT-CONSUMER-{self.consumer_id}] ✅ Alert forwarded to {self.endpoint}")
                        return
                    else:
                        logger.warning(f"[ALERT-CONSUMER-{self.consumer_id}] ❌ Failed to forward alert: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"[ALERT-CONSUMER-{self.consumer_id}] Request error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        
        except Exception as e:
            logger.error(f"[ALERT-CONSUMER-{self.consumer_id}] Error: {e}")

def main():
    """Main entry point - creates exactly 3 consumer groups as specified"""
    all_consumers = []
    
    try:
        # Consumer Group 1: 3 consumers for sensor-data topic
        data_consumers = []
        for i in range(3):
            consumer = DataConsumer(
                topic=KAFKA_TOPIC_DATA,
                group_id='sensor-data-consumers',  # Same group ID for all 3
                consumer_id=i+1
            )
            data_consumers.append(consumer)

        # Consumer Group 2: 1 consumer for email alerts
        email_consumer = AlertConsumer(
            topic=KAFKA_TOPIC_ALERTS,
            group_id='email-alert-consumers',
            alert_type='email',
            endpoint='email',
            consumer_id=1
        )

        # Consumer Group 3: 1 consumer for notification alerts  
        notification_consumer = AlertConsumer(
            topic=KAFKA_TOPIC_ALERTS,
            group_id='notification-alert-consumers',
            alert_type='notification',
            endpoint='notify',
            consumer_id=1
        )

        # Start all consumers in threads
        all_consumers = data_consumers + [email_consumer, notification_consumer]
        threads = []

        for consumer in all_consumers:
            thread = threading.Thread(
                target=consumer.run,
                daemon=True,
                name=f"{consumer.group_id}-{consumer.consumer_id}"
            )
            threads.append(thread)
            thread.start()
            logger.info(f"Started {thread.name}")

        logger.info(f"""
        ✅ Consumer Groups Configuration:
        📊 Group 1 (sensor-data-consumers): 3 consumers
        📧 Group 2 (email-alert-consumers): 1 consumer  
        🔔 Group 3 (notification-alert-consumers): 1 consumer
        """)

        # Wait for all threads
        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        logger.info("Shutting down all consumer groups...")
        # Stop all consumers gracefully
        for consumer in all_consumers:
            consumer.running = False
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nShutting down consumers...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
