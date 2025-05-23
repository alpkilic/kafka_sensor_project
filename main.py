import uvicorn
from src.api import app
from src.helpers.settings import API_HOST, API_PORT
from src.helpers.logger import get_logger

logger = get_logger("main")

if __name__ == "__main__":
    logger.info("Starting Sensor Data Processing System...")
    uvicorn.run(app, host=API_HOST, port=API_PORT)