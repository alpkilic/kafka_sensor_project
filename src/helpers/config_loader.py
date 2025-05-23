import json
import os
from typing import Dict, Any

def load_config(filename: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', filename)
    with open(config_path, 'r') as f:
        return json.load(f)

# Load configurations
THRESHOLDS = load_config('thresholds.json')
SENSOR_MAPPINGS = load_config('sensor_mappings.json')
KAFKA_CONFIG = load_config('kafka_config.json')

# Environment-based settings
ENV_CONFIG = {
    "kafka": {
        "bootstrap_servers": os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    },
    "api": {
        "host": os.getenv('API_HOST', '0.0.0.0'),
        "port": int(os.getenv('API_PORT', '8000')),
        "url": os.getenv('API_URL', 'http://localhost:8000')
    },
    "database": {
        "user": os.getenv('POSTGRES_USER', 'postgres'),
        "password": os.getenv('POSTGRES_PASSWORD', 'postgres'),
        "host": os.getenv('POSTGRES_HOST', 'localhost'),
        "port": os.getenv('POSTGRES_PORT', '5432'),
        "name": os.getenv('POSTGRES_DB', 'sensordb')
    }
}

# Generate database URL
DB_URL = f"postgresql://{ENV_CONFIG['database']['user']}:{ENV_CONFIG['database']['password']}@{ENV_CONFIG['database']['host']}:{ENV_CONFIG['database']['port']}/{ENV_CONFIG['database']['name']}"