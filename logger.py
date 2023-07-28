import logging
import os
from datetime import date
from dotenv import load_dotenv, find_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv(find_dotenv())

# Check if the LOG_DIR and LOG_LEVEL environment variables are set
LOG_DIR = os.getenv('LOG_DIR')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

# Create a mapping of log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

if not LOG_DIR:
    # If not, default to a logs directory in the same location as this script
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

# Create the log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(script_name):
    # Create a logger with the script name
    logger = logging.getLogger(script_name)

    # Set the log level to record all messages
    logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.DEBUG))

    # Create a file handler that logs debug and higher level messages to a file
    log_file = os.path.join(LOG_DIR, f"{script_name}_{date.today().isoformat()}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=5000, backupCount=5)
    file_handler.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.DEBUG))

    # Create a console handler that logs error and higher level messages to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.DEBUG))

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
