from logger import setup_logger
from dotenv import load_dotenv
import os
import psycopg2
import numpy as np
from psycopg2.extras import register_uuid
import uuid
import openai

logger = setup_logger(__name__)

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

class Setting:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
        # Store OpenAI api key, may add other LLM support later
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY is not set in the .env file.")
            raise EnvironmentError("OPENAI_API_KEY is not set in the .env file.")
        
        # Verify the OpenAI API key by making a test API call
        self.verify_openai_api_key()

        # Store input and output directory paths
        self.input_dir = os.getenv('INPUT_DIR')
        self.output_dir = os.getenv('OUTPUT_DIR')

        # Verify if input and output directories exist
        if not self.input_dir or not os.path.exists(self.input_dir):
            logger.error("The input directory (INPUT_DIR) does not exist. Please create the directory and set it in the .env file.")
            raise EnvironmentError("The input directory (INPUT_DIR) does not exist. Please create the directory and set it in the .env file.")

        if not self.output_dir or not os.path.exists(self.output_dir):
            logger.error("The output directory (OUTPUT_DIR) does not exist. Please create the directory and set it in the .env file.")
            raise EnvironmentError("The output directory (OUTPUT_DIR) does not exist. Please create the directory and set it in the .env file.")

    def verify_openai_api_key(self):
        """Verify the OpenAI API key by making a test API call."""
        try:
            # Set the API key for the openai library
            openai.api_key = self.openai_api_key

            # Make a test call to the OpenAI API
            openai.Completion.create(engine="text-davinci-002", prompt="test")
            logger.info("OpenAI API key is valid.")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            raise ValueError(f"Failed to connect to OpenAI: {e}")

class DatabaseConfig:
    DATABASE = os.getenv('DATABASE')

    @staticmethod
    def get_database_config():
        if DatabaseConfig.DATABASE == 'pg':
            return {
                'host': os.getenv('PG_HOST'),
                'port': os.getenv('PG_PORT'),
                'user': os.getenv('PG_USER'),
                'password': os.getenv('PG_PASS'),
                'dbname': 'cognimesh'
            }
        # Add other database configurations as elif statements
        else:
            raise ValueError("Unsupported database type")

class PGDocStore:    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.connect()
    
    def connect(self):
        register_uuid()
        self.connection = psycopg2.connect(**self.config)
    
    def get_cursor(self):
        # Ensure the connection is alive
        self.ensure_connection()
        return self.connection.cursor()
    
    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def ensure_connection(self):
        if self.connection.closed:
            # Re-establish the connection if it's closed
            self.connection = psycopg2.connect(**self.config)

    def close_connection(self):
        self.connection.close()

class Store:
    def __init__(self):
        config = DatabaseConfig.get_database_config()
        if DatabaseConfig.DATABASE == 'pg':
            self.db = PGDocStore(config)
        # Add other database initializations as elif statements

    def get_db(self):
        return self.db
    
# Global store instance
store = Store().get_db()