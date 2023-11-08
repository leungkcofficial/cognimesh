from logger import setup_logger
from dotenv import load_dotenv
import os
import psycopg2
import numpy as np
from psycopg2.extras import register_uuid
import uuid

logger = setup_logger(__name__)

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

class Setting:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
        # Store OpenAI api key, may add other LLM support later
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        # Store Postgresql connection parameters, may add other
        # self.database = os.getenv('DATABASE')
        # self.pg_host = os.getenv('PG_HOST')
        # self.pg_port = os.getenv('PG_PORT')
        # self.pg_user = os.getenv('PG_USER')
        # self.pg_password = os.getenv('PG_PASS')
        # self.pg_dbname = 'cognimesh'

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