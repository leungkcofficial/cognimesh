from logger import setup_logger
from dotenv import load_dotenv
import os
import psycopg2
import numpy as np
from ..axon.in_come import File
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
    
    def add_document(self, file:File):
        conn = self.conn
        # Create a cursor object
        cur = conn.cursor()
        with conn.cursor() as cur:
            try:
                cur.execute("""INSERT INTO documents (file_path, file_name, file_size, file_sha1, file_extension, chunk_size, chunk_overlap) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING doc_id""", 
                           (file.file_path, file.file_name, file.file_size, file.file_sha1, file.file_extension, file.chunk_size, file.chunk_overlap))
                doc_id = cur.fetchone()[0]
                conn.commit()
                return doc_id
            except Exception as e:
                conn.rollback()
                logger.error(f"An error occurred while adding document: {e}")
                raise
            
    def add_vectors(self, doc_id, embed):
        conn = self.conn
        with conn.cursor() as cur:
            vector_ids = []  # To store the generated vector UUIDs
            template = """INSERT INTO vectors (vector_id, doc_id, vector_index, embeddings, created_at)
                          VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) RETURNING vector_id"""
            try:
                for vector_index, vector_data in enumerate(embed):
                    # Convert the NumPy array to a Python list
                    vector_data_list = vector_data.tolist() if isinstance(vector_data, np.ndarray) else vector_data
                    vector_id = uuid.uuid4()
                    cur.execute(template, (vector_id, doc_id, vector_index, vector_data_list))
                    vector_ids.append(cur.fetchone()[0])  # Fetch the returned vector_id
                conn.commit()
                return vector_ids
            except Exception as e:
                conn.rollback()
                logger.error(f"An error occurred while adding vectors: {e}")
                raise

    def update_document_vectors(self, doc_id, vector_ids):
        conn = self.conn
        with conn.cursor() as cur:
            try:
                # No need to convert to string or use ARRAY construction, psycopg2 can handle list of UUIDs
                cur.execute("""UPDATE documents SET vectors_ids = %s WHERE doc_id = %s""",
                            (vector_ids, doc_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"An error occurred while updating document vectors: {e}")
                raise

    def ensure_connection(self):
        if self.conn.closed:
            # Re-establish the connection if it's closed
            self.conn = psycopg2.connect(self.connection_string)

    def close_connection(self):
        self.conn.close()
