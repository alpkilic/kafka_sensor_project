# Real-time Sensor Data Processing System

## Overview

This project is a comprehensive real-time sensor data processing system built with Apache Kafka, FastAPI, and PostgreSQL. The system collects, processes, and analyzes data from multiple sensor types across various locations, detects critical readings, and generates appropriate alerts.

## Features

- **Multi-sensor Support**: Process data from temperature, humidity, traffic, and air-quality sensors
- **Real-time Processing**: Stream processing with Kafka for immediate data handling
- **Critical Alert System**: Automatic detection and notification of critical sensor readings
- **Distributed Architecture**: Scalable design with multiple consumers and partitioned topics
- **Data Analysis**: Historical data querying and trend analysis
- **Realistic Data Simulation**: Built-in simulator for testing and demonstration

## Technology Stack

- **Messaging**: Apache Kafka
- **API**: FastAPI
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose
- **Language**: Python 3.11

## System Architecture

The system uses an event-driven architecture with the following components:

1. **Sensor Simulator**: Generates realistic sensor data with configurable distributions
2. **REST API**: Provides endpoints for data ingestion and retrieval
3. **Kafka Broker**: Handles message streaming with dedicated topics for normal and critical data
4. **Consumer Groups**: Process incoming data with parallel processing capabilities
5. **PostgreSQL Database**: Stores both raw and processed sensor readings

## Data Flow

```
Simulator → API → Kafka Producer → Kafka Topics → Consumers → Database
                                              ↓
                                        Alert System
```

1. The simulator generates data from 20 sensors across 4 sensor types
2. Data is sent to the API service
3. API validates data and publishes to appropriate Kafka topic
4. Data consumers process and store readings in the database
5. Critical values trigger alert consumers for notifications/emails

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Network access for Docker containers

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd kafka_sensor_project

# Start all services
docker-compose up -d

# Check that all services are running
docker-compose ps

# Check system health
curl http://localhost:8000/health
```

### Manual Startup (Development)

For development purposes, you can start the services individually:

```bash
# Start infrastructure components
docker-compose up -d zookeeper kafka postgres

# Create Kafka topics
docker-compose up kafka-setup

# Start application components
docker-compose up -d api
docker-compose up -d consumer
docker-compose up -d simulator
```

## API Endpoints

### Health Check

```
GET /health
```

Checks the health of the API server, Kafka connection, and database connection.

### Publish Sensor Data

```
POST /api/publish
```

Publishes new sensor data to the appropriate Kafka topic.

Example request:
```json
{
  "sensor_id": "temp_1",
  "type": "temperature",
  "location": "New York",
  "value": 28.5,
  "timestamp": "2025-05-23T14:25:43"
}
```

### Create Notification

```
POST /api/notify
```

Creates a notification for critical sensor readings.

### Send Email Alert

```
POST /api/email
```

Generates an email alert for critical sensor readings.

### Data Analysis

```
GET /api/analysis?sensor_type=temperature&location=New York
```

Retrieves analysis of sensor data with optional filtering by type and location.

## Configuration

The system is configured via JSON files in the `src/config` directory:

- **app_config.json**: General application settings
- **kafka_config.json**: Kafka topic configuration and partition mapping
- **sensor_mappings.json**: Maps sensor IDs to physical locations
- **thresholds.json**: Defines critical thresholds for each sensor type

## Sensor Types

The system supports four types of sensors:

1. **Temperature**
   - Unit: °C (Celsius)
   - Normal range: 15-35°C
   - Critical threshold: >45°C

2. **Humidity**
   - Unit: % (Percentage)
   - Normal range: 30-60%
   - Critical thresholds: <20% or >75%

3. **Traffic**
   - Unit: vehicles/hour
   - Normal range: 100-300 vehicles/hour
   - Critical threshold: >350 vehicles/hour

4. **Air Quality**
   - Unit: AQI (Air Quality Index)
   - Normal range: 0-100 AQI
   - Critical threshold: >150 AQI

## Monitoring

### Kafka Partition Monitoring

```bash
python src/monitor_partitions.py
```

This displays real-time data flowing through specific Kafka partitions.

### Service Logs

```bash
# View logs from all services
docker-compose logs -f

# View logs from a specific service
docker-compose logs -f api
docker-compose logs -f consumer
docker-compose logs -f simulator
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker exec -it sensor-postgres psql -U postgres -d sensordb

# Query processed data
SELECT * FROM processed_data ORDER BY processed_at DESC LIMIT 10;

# Query critical events
SELECT * FROM processed_data WHERE status = 'critical';
```

## Troubleshooting

### Common Issues

1. **Service not starting**: Check Docker logs for that service
   ```bash
   docker-compose logs <service-name>
   ```

2. **API Connection Issues**: Verify network connectivity
   ```bash
   curl http://localhost:8000/health
   ```

3. **Kafka Connection Issues**: Check Kafka broker status
   ```bash
   docker-compose restart kafka
   docker exec sensor-kafka kafka-topics --bootstrap-server localhost:9092 --list
   ```

4. **Database Connection Issues**: Verify PostgreSQL is running
   ```bash
   docker-compose restart postgres
   docker exec sensor-postgres pg_isready
   ```

## Development

### Project Structure

```
kafka_sensor_project/
├── docker-compose.yaml      # Docker service definitions
├── Dockerfile               # Container build instructions
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── src/
│   ├── api.py               # FastAPI endpoints
│   ├── consumer.py          # Kafka consumer groups
│   ├── database.py          # PostgreSQL operations
│   ├── models.py            # Pydantic data models
│   ├── monitor_partitions.py# Kafka monitoring tool
│   ├── service.py           # Business logic & Kafka producer
│   ├── simulator.py         # Sensor data generator
│   ├── helpers/
│   │   ├── logger.py        # Logging configuration
│   │   ├── settings.py      # Environment settings
│   │   └── utils.py         # Utility functions
│   └── config/
│       ├── app_config.json  # Application settings
│       ├── kafka_config.json# Kafka configuration
│       ├── sensor_mappings.json# Sensor location mapping
│       └── thresholds.json  # Critical threshold values
└── logs/                    # Application logs
```

### Local Development

For development purposes, you may want to run services locally:

1. Create and activate a Python virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables or use a `.env` file
4. Run infrastructure in Docker: `docker-compose up -d zookeeper kafka postgres`
5. Run application components separately:
   - `python main.py`
   - `python -m src.consumer`
   - `python -m src.simulator`

## License

[Insert License Information Here]

## Authors

[Insert Author Information Here]

## Acknowledgements

- Apache Kafka
- FastAPI
- PostgreSQL
- The Python community