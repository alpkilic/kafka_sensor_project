import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    create_engine, 
    Column, 
    Integer, 
    String, 
    Float, 
    DateTime, 
    Text, 
    Boolean,
    UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from src.helpers.settings import DB_URL, SENSOR_MAPPINGS
from src.helpers.logger import get_logger
from src.helpers.utils import (
    get_comfort_level, 
    get_humidity_level, 
    get_traffic_level, 
    get_air_quality_level, 
    get_unit
)

# Set up logging
logger = get_logger("database")

# Define SQLAlchemy Base
Base = declarative_base()

class RawData(Base):
    """Raw sensor data table"""
    __tablename__ = 'raw_data'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(50), nullable=False)
    sensor_type = Column(String(20), nullable=False)
    location = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProcessedData(Base):
    __tablename__ = 'processed_data'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(50), nullable=False)
    sensor_type = Column(String(20), nullable=False)
    location = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(String(50), nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False)
    additional_data = Column(Text, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('sensor_id', 'timestamp', name='uix_sensor_timestamp'),
    )

# Create database engine and tables
engine = create_engine(DB_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def init_db(max_retries=30, retry_delay=2):
    """Initialize database with retry logic"""
    for attempt in range(max_retries):
        try:
            # Drop and recreate all tables
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            
            # Verify tables exist
            with engine.connect() as conn:
                tables = ['raw_data', 'processed_data']
                for table in tables:
                    result = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
                    exists = result.scalar()
                    if not exists:
                        raise Exception(f"Table {table} was not created")
            
            logger.info("Successfully connected to database and verified tables")
            return True
        except Exception as e:
            logger.warning(f"Database initialization attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Failed to initialize database after maximum retries")
                raise

# Initialize database
init_db()

def store_raw_data(sensor_data: Dict) -> bool:
    """Store raw sensor data in database"""
    session = Session()
    
    try:
        # Create new raw data record
        new_raw_data = RawData(
            sensor_id=sensor_data["sensor_id"],
            sensor_type=sensor_data["type"],
            location=sensor_data["location"],
            value=sensor_data["value"],
            timestamp=sensor_data["timestamp"]
        )
        
        # Add to session and commit
        session.add(new_raw_data)
        session.commit()
        
        logger.info(f"Stored raw data: {sensor_data['sensor_id']} in database")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to store raw data: {e}")
        return False
        
    finally:
        session.close()

def process_sensor_data(sensor_data: Dict) -> Dict:
    """Process raw sensor data - All data from sensor-data topic is NORMAL"""
    try:
        # Start with the base data
        processed = sensor_data.copy()
        
        # Add processing timestamp
        processed["processed_at"] = datetime.now().isoformat()
        
        # sensor-data topic'inden gelen TÜM DATA NORMAL!
        processed["status"] = "normal"
        processed["is_critical"] = False
        
        # Sensor-specific processing
        sensor_type = sensor_data["type"]
        value = sensor_data["value"]
        
        if sensor_type == "temperature":
            processed["celsius"] = value
            processed["fahrenheit"] = (value * 9/5) + 32
            processed["comfort_level"] = get_comfort_level(value)
            
        elif sensor_type == "humidity":
            processed["relative_humidity"] = value
            processed["comfort_level"] = get_humidity_level(value)
            
        elif sensor_type == "traffic":
            processed["vehicles_per_hour"] = value
            processed["congestion_level"] = get_traffic_level(value)
            
        elif sensor_type == "air-quality":
            processed["aqi"] = value
            processed["health_impact"] = get_air_quality_level(value)
        
        return processed
        
    except Exception as e:
        logger.error(f"Error in process_sensor_data: {e}")
        raise

def store_processed_data(processed_data: Dict) -> bool:
    """Store processed sensor data - ALWAYS NORMAL STATUS"""
    session = Session()
    
    try:
        # Check for duplicates
        existing = session.query(ProcessedData).filter(
            ProcessedData.sensor_id == processed_data['sensor_id'],
            ProcessedData.timestamp == processed_data['timestamp']
        ).first()
        
        if existing:
            logger.debug(f"Duplicate record found for {processed_data['sensor_id']} at {processed_data['timestamp']}")
            return False
        
        # Get correct location from SENSOR_MAPPINGS
        try:
            correct_location = SENSOR_MAPPINGS[processed_data['type']][processed_data['sensor_id']]
        except KeyError:
            logger.error(f"Invalid sensor configuration: {processed_data['type']}, {processed_data['sensor_id']}")
            return False
        
        # ALWAYS NORMAL - sensor-data topic only contains normal data
        status = "normal"
        
        new_data = ProcessedData(
            sensor_id=processed_data['sensor_id'],
            sensor_type=processed_data['type'],
            location=correct_location,
            value=processed_data['value'],
            timestamp=processed_data['timestamp'],
            processed_at=datetime.now(),
            status=status,  # Always "normal"
            additional_data=json.dumps(processed_data)
        )
        
        session.add(new_data)
        session.commit()
        
        logger.info(f"Stored normal data for sensor {processed_data['sensor_id']} with value {processed_data['value']}")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Database error while storing processed data: {str(e)}")
        return False
    finally:
        session.close()

def get_analysis(sensor_type: Optional[str] = None, location: Optional[str] = None) -> Dict:
    """Get analysis from processed data"""
    session = Session()
    
    try:
        # Build query for processed data
        query = session.query(ProcessedData)
        
        # Add filters
        if sensor_type:
            query = query.filter(ProcessedData.sensor_type == sensor_type)
        
        if location:
            query = query.filter(ProcessedData.location == location)
        
        # Execute query
        filtered_data = query.all()
        
        if not filtered_data:
            return {
                "sensor_type": sensor_type,
                "location": location,
                "data_points": 0,
                "time_range": {"start": None, "end": None},
                "average_value": 0,
                "max_value": 0,
                "min_value": 0,
                "critical_events": 0,
                "trend": "insufficient data",
                "insights": ["No data available for analysis"]
            }
        
        # Extract values for analysis
        values = [d.value for d in filtered_data]
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)
        
        # Count critical events (should be 0 for normal data)
        critical_events = sum(1 for d in filtered_data if d.status == 'critical')
        
        # Get time range
        timestamps = [datetime.fromisoformat(d.timestamp) for d in filtered_data]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        # Determine trend (simple analysis)
        trend = "stable"
        if len(filtered_data) > 1:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            if second_half > first_half * 1.1:
                trend = "increasing"
            elif second_half < first_half * 0.9:
                trend = "decreasing"
        
        # Generate insights
        insights = []
        
        if trend == "increasing":
            insights.append("Values are trending upward")
        elif trend == "decreasing":
            insights.append("Values are trending downward")
        else:
            insights.append("Values are stable")
        
        if max_value > avg_value * 1.5:
            insights.append(f"Significant spike detected (max: {max_value})")
        
        if min_value < avg_value * 0.5:
            insights.append(f"Significant drop detected (min: {min_value})")
        
        if len(filtered_data) < 5:
            insights.append("Limited data available - analysis may not be reliable")
        
        # Note: critical_events should always be 0 for sensor-data topic
        if critical_events > 0:
            insights.append(f"WARNING: Found {critical_events} critical events in normal data - this should not happen!")
        
        return {
            "sensor_type": sensor_type,
            "location": location,
            "data_points": len(filtered_data),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "average_value": round(avg_value, 2),
            "max_value": max_value,
            "min_value": min_value,
            "critical_events": critical_events,
            "trend": trend,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error analyzing data: {e}")
        return {
            "error": str(e),
            "sensor_type": sensor_type,
            "location": location,
            "data_points": 0,
            "time_range": {"start": None, "end": None},
            "average_value": 0,
            "max_value": 0,
            "min_value": 0,
            "critical_events": 0,
            "trend": "error",
            "insights": ["Error occurred during analysis"]
        }
        
    finally:
        session.close()