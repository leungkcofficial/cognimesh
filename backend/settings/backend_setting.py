from logger import setup_logger
from dotenv import load_dotenv
import os
import psycopg2
import numpy as np
from psycopg2.extras import register_uuid
import uuid
import openai
from langchain.embeddings.openai import OpenAIEmbeddings

logger = setup_logger(__name__)

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

class Setting:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
        # Store OpenAI api key, may add other LLM support later
        
        # Load embedding model setting
        self.embedding_model = os.getenv('EMBEDDING_MODEL')
        if self.embedding_model not in ['openai', 'other_model']:  # Add other models as needed
            logger.error("Unsupported embedding model in .env file.")
            raise EnvironmentError("Unsupported embedding model in .env file.")
        
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

    def similarity_search(self, query_embedding, match_threshold=0.8, match_count=5):
        """
        Perform a similarity search in the database using vector embeddings.

        Args:
            query_embedding (list): The embedding vector of the query document.
            match_threshold (float): The threshold for matching similarity (default is 0.8).
            match_count (int): The number of matches to return (default is 5).

        Returns:
            list: A list of tuples containing matched document IDs, content, and similarity scores.

        Raises:
            psycopg2.DatabaseError: If a database error occurs.
        """
        try:
            with self.connection.cursor() as cursor:
                # Call the match_documents function in the database
                cursor.callproc('match_documents', [query_embedding, match_threshold, match_count])
                matches = cursor.fetchall()
                return matches
        except psycopg2.DatabaseError as e:
            logger.error(f"Database error during similarity search: {e}")
            raise e

class Store:
    def __init__(self):
        config = DatabaseConfig.get_database_config()
        if DatabaseConfig.DATABASE == 'pg':
            self.db = PGDocStore(config)
        # Add other database initializations as elif statements

    def get_db(self):
        return self.db

class EmbeddingService:
    def __init__(self, setting: Setting):
        self.setting = setting
        if self.setting.embedding_model == 'openai':
            self.embedder = OpenAIEmbeddings(openai_api_key=self.setting.openai_api_key)
        # Add other models here
        else:
            logger.error(f"Unsupported embedding model: {self.setting.embedding_model}")
            raise NotImplementedError(f"Embedding model {self.setting.embedding_model} is not implemented")

    def embed_documents(self, documents):
        """
        Embeds the given documents using the selected embedding model.

        Args:
            documents (List[str]): A list of document texts to be embedded.

        Returns:
            List: A list of embedding vectors for the provided documents.

        Raises:
            Exception: If an error occurs during the embedding process.
        """
        try:
            return self.embedder.embed_documents(documents)
        except Exception as e:
            logger.error(f"Error during document embedding: {e}")
            raise e

setting = Setting()
# Global store instance
store = Store().get_db()
# Global embedding instance
embedding = EmbeddingService(setting)