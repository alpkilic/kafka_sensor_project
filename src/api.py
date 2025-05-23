from fastapi import FastAPI, HTTPException, Query
from typing import Optional, Dict
from sqlalchemy.sql import text
from src.models import SensorData, NotificationPayload, EmailPayload, AnalysisResponse
from src.service import sensor_service  # Import the instance instead of module
from src import database
from src.helpers.logger import get_logger

# Set up logging
logger = get_logger("api")

# Create FastAPI app
app = FastAPI(title="Sensor Data Processing System", version="1.0.0")

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to the Sensor Data Processing System"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Try to connect to Kafka and Postgres
        sensor_service.init_kafka()  
        with database.Session() as session:
            session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "api_version": "1.0.0",
            "kafka": "connected",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/api/publish")
def publish_sensor_data(sensor_data: SensorData):
    """Publish sensor data to Kafka topics based on criticality"""
    try:
        result = sensor_service.publish_data(sensor_data.dict())  
        logger.info(f"Successfully published sensor data: {sensor_data.sensor_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to publish sensor data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notify", response_model=NotificationPayload)
def notify_alert(alert_data: SensorData):
    """Create notification for critical alert"""
    if not alert_data.is_critical():
        raise HTTPException(status_code=400, detail="Data is not critical")
    
    notification = sensor_service.create_notification(alert_data.dict())
    return notification

@app.post("/api/email", response_model=EmailPayload)
def email_alert(alert_data: SensorData):
    """Create email for critical alert"""
    if not alert_data.is_critical():
        raise HTTPException(status_code=400, detail="Data is not critical")
    
    email = sensor_service.handle_email(alert_data)  # Use the instance method
    return email

@app.get("/api/analysis", response_model=AnalysisResponse)
def get_analysis(
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """Get sensor data analysis"""
    return sensor_service.get_analysis(sensor_type, location)  # Use the instance method