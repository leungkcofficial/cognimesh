from logger import setup_logger
from dotenv import load_dotenv
import os

logger = setup_logger(__name__)

class Setting:
    """
    This class is responsible for loading and providing access to configuration settings from the environment file.

    Attributes:
        embedding_model (str): The selected embedding model.
        openai_api_key (str): API key for OpenAI services.
        input_dir (str): Directory path for input files.
        output_dir (str): Directory path for output files.
        database_type (str): Type of database being used.
    """

    def __init__(self):
        """
        Initializes the Setting class and loads environment variables.
        """
        try:
            load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
            self.embedding_model = os.getenv('EMBEDDING_MODEL')
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            self.input_dir = os.getenv('INPUT_DIR')
            self.output_dir = os.getenv('OUTPUT_DIR')
            self.database_type = os.getenv('DATABASE')
        except Exception as e:
            logging.error(f"Error loading environment variables: {e}")
            raise e
        
    def get_database_config(self):
        """
        Get the database configuration based on the environment settings.

        Returns:
            dict: Database configuration dictionary.

        Raises:
            ValueError: If the database type is not supported.
        """
        if self.database_type == 'pg':
            return {
                'host': os.getenv('PG_HOST'),
                'port': os.getenv('PG_PORT'),
                'user': os.getenv('PG_USER'),
                'password': os.getenv('PG_PASS'),
                'dbname': 'cognimesh'
            }
        else:
            # Handle other database types here
            logger.error(f"Unsupported database type: {self.database_type}")
            raise ValueError(f"Unsupported database type: {self.database_type}")