from logger import setup_logger
from .settings import Setting
import psycopg2
from psycopg2.extras import register_uuid

logger = setup_logger(__name__)

# # Load environment variables from .env file
# load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# class DatabaseConfig:
#     DATABASE = os.getenv('DATABASE')

#     @staticmethod
#     def get_database_config():
#         if DatabaseConfig.DATABASE == 'pg':
#             return {
#                 'host': os.getenv('PG_HOST'),
#                 'port': os.getenv('PG_PORT'),
#                 'user': os.getenv('PG_USER'),
#                 'password': os.getenv('PG_PASS'),
#                 'dbname': 'cognimesh'
#             }
#         # Add other database configurations as elif statements
#         else:
#             raise ValueError("Unsupported database type")

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
    """
    This class manages the database connections and operations.

    Attributes:
        db (object): Instance of the database class being used.
    """

    def __init__(self, setting: Setting):
        """
        Initializes the Store class with a database configuration based on the provided settings.

        Args:
            setting (Setting): The setting instance containing configuration details.
        """
        try:
            # Retrieve the database configuration based on the type of database
            config = setting.get_database_config()
            if setting.database_type == 'pg':
                self.db = PGDocStore(config)
            else:
                raise ValueError("Unsupported database type")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise e

    def get_db(self):
        """
        Returns the database instance.

        Returns:
            object: The database instance.
        """
        return self.db

# Global store instance
setting = Setting()
store = Store(setting).get_db()