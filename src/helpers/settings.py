from src.helpers.config_loader import (
    THRESHOLDS,
    SENSOR_MAPPINGS,
    KAFKA_CONFIG,
    ENV_CONFIG,
    DB_URL
)

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = ENV_CONFIG['kafka']['bootstrap_servers']
KAFKA_TOPIC_ALERTS = KAFKA_CONFIG['topic_alerts']
KAFKA_TOPIC_DATA = KAFKA_CONFIG['topic_data']
PARTITION_MAPPING = KAFKA_CONFIG['partition_mapping']

# API settings
API_HOST = ENV_CONFIG['api']['host']
API_PORT = ENV_CONFIG['api']['port']
API_URL = ENV_CONFIG['api']['url']

# Export all configurations
__all__ = [
    'THRESHOLDS',
    'SENSOR_MAPPINGS',
    'KAFKA_BOOTSTRAP_SERVERS',
    'KAFKA_TOPIC_ALERTS',
    'KAFKA_TOPIC_DATA',
    'PARTITION_MAPPING',
    'API_HOST',
    'API_PORT',
    'API_URL',
    'DB_URL'
]