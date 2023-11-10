# plugins/zotero_connect.py

from ..settings.plugin import PluginInterface
from ..settings.backend_setting import store  # Import store to access the database connection
from logger import setup_logger
import os
import json

# Setup a logger for this plugin
logger = setup_logger('zotero_connect')

class ZoteroConnect(PluginInterface):
    """
    Plugin for connecting to Zotero and managing academic journals and books metadata.
    """

    def setup(self, config):
        """
        Set up the ZoteroConnect plugin, ensuring database tables are present and correctly structured.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary with necessary API details and paths.

        Raises:
            Exception: If any step in the setup process fails.
        """
        logger.info("Setting up ZoteroConnect plugin.")

        # Load .env variables for Zotero
        zotero_api_base_url = os.getenv('ZOTERO_API_BASE_URL')
        zotero_library_id = os.getenv('ZOTERO_LIBRARY_ID')
        zotero_api_key = os.getenv('ZOTERO_API_KEY')

        if not all([zotero_api_base_url, zotero_library_id, zotero_api_key]):
            logger.error("Zotero API environment variables are not set.")
            raise ValueError("Zotero API environment variables are not set in the .env file.")

        # Check database connection
        db_connection = store.connection

        try:
            with db_connection.cursor() as cursor:
                # Check if tables exist and have correct columns
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'zotero_articles'
                    );
                """)
                articles_table_exists = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'zotero_books'
                    );
                """)
                books_table_exists = cursor.fetchone()[0]

                # If tables don't exist or structure is incorrect, drop and recreate
                if not articles_table_exists or not books_table_exists:
                    logger.info("Creating zotero_articles and zotero_books tables.")
                    cursor.execute("DROP TABLE IF EXISTS zotero_articles, zotero_books;")
                    cursor.execute("""
                        CREATE TABLE zotero_articles (
                            doc_id UUID PRIMARY KEY,
                            doi VARCHAR(255),
                            metadata JSONB,
                            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
                        );
                    """)
                    cursor.execute("""
                        CREATE TABLE zotero_books (
                            doc_id UUID PRIMARY KEY,
                            isbn VARCHAR(255),
                            metadata JSONB,
                            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
                        );
                    """)
                    db_connection.commit()
                else:
                    # Check columns of existing tables
                    # Here you'd check that each table has the exact columns you expect
                    # This is a simplified version of such a check
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'zotero_articles'")
                    articles_columns = [row[0] for row in cursor.fetchall()]
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'zotero_books'")
                    books_columns = [row[0] for row in cursor.fetchall()]
                    expected_columns = ['doc_id', 'metadata']
                    if not all(col in articles_columns for col in expected_columns + ['doi']) or not all(col in books_columns for col in expected_columns + ['isbn']):
                        logger.error("Table structure for zotero_articles or zotero_books is incorrect.")
                        raise Exception("Table structure is incorrect.")

            self.switch(True)  # Enable the plugin
            logger.info("ZoteroConnect plugin setup completed successfully.")
        except Exception as e:
            db_connection.rollback()
            logger.error(f"An error occurred during setup: {e}")
            raise e

    def switch(self, enable: bool) -> None:
        """
        Enable or disable the ZoteroConnect plugin.

        Args:
            enable (bool): True to enable the plugin, False to disable it.
        """
        self.enabled = enable
        action = "enabled" if enable else "disabled"
        logger.info(f"ZoteroConnect plugin has been {action}.")

    def delete(self) -> None:
        """
        Disable the ZoteroConnect plugin and clean up any resources it created, 
        such as database tables, webpages, or frontend components.
        """
        if self.enabled:
            self.switch(False)  # Ensure the plugin is disabled before deletion

        db_connection = store.connection
        try:
            with db_connection.cursor() as cursor:
                # Drop the plugin's database tables
                cursor.execute("""
                    DROP TABLE IF EXISTS zotero_articles;
                    DROP TABLE IF EXISTS zotero_books;
                """)
                db_connection.commit()
                logger.info("ZoteroConnect plugin tables and resources have been deleted.")
        except Exception as e:
            db_connection.rollback()
            logger.error(f"Failed to delete ZoteroConnect plugin tables: {e}")
            raise e