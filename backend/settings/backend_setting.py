from logger import setup_logger
from dotenv import load_dotenv
import os
import psycopg2
import numpy as np
from psycopg2.extras import register_uuid
import uuid

# from ..neuron.neuron import Memory

logger = setup_logger(__name__)

class Setting:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
        # Store OpenAI api key, may add other LLM support later
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        # Store Postgresql connection parameters, may add other
        self.database = os.getenv('DATABASE')
        self.pg_host = os.getenv('PG_HOST')
        self.pg_port = os.getenv('PG_PORT')
        self.pg_user = os.getenv('PG_USER')
        self.pg_password = os.getenv('PG_PASS')
        self.pg_dbname = 'cognimesh'
            
class PGDocStore:
    def __init__(self):
        setting = Setting()
        if not setting.database == 'pg':
            raise ValueError(f"Database is not Postgresql.")
        
        else:
            register_uuid()
            self.conn = psycopg2.connect(dbname = setting.pg_dbname,
                                         user = setting.pg_user,
                                         password = setting.pg_password,
                                         host = setting.pg_host,
                                         port = setting.pg_port)
            self.doc_table = "documents"
            self.vec_table = "vectors"
    
    def get_cursor(self):
        # Ensure the connection is alive
        self.ensure_connection()
        return self.conn.cursor()
    
    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def ensure_connection(self):
        if self.conn.closed:
            # Re-establish the connection if it's closed
            self.conn = psycopg2.connect(self.connection_string)

    def close_connection(self):
        self.conn.close()
