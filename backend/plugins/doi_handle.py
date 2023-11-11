from ..settings.plugin import PluginInterface
from ..settings.storage import store# Import store to access the database connection
from typing import Any, Optional, List
from logger import setup_logger
import os
import json

# Setup a logger for this plugin
logger = setup_logger(__name__)

class DOIHandle(PluginInterface):
    """
    A plugin for detecting DOI in documents and retrieving metadata from CrossRef.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logger(__name__)
    
    def setup(self, config):
        """
        ensuring database tables are present and correctly structured.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary with necessary API details and paths.

        Raises:
            Exception: If any step in the setup process fails.
        """
        logger.info("Setting up DOIHandle plugin.")

        # Check database connection
        db_connection = store.connection

        try:
            with db_connection.cursor() as cursor:
                # Check if tables exist and have correct columns
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'articles_doi'
                    );
                """)
                articles_table_exists = cursor.fetchone()[0]

                # If tables don't exist or structure is incorrect, drop and recreate
                if not articles_table_exists:
                    logger.info("Creating articles_doi table.")
                    cursor.execute("DROP TABLE IF EXISTS articles_doi;")
                    cursor.execute("""
                        CREATE TABLE articles_doi (
                            doc_id UUID PRIMARY KEY,
                            doi VARCHAR(255),
                            metadata JSONB,
                            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
                        );
                    """)
                    db_connection.commit()
                else:
                    # Check columns of existing tables
                    # Here you'd check that each table has the exact columns you expect
                    # This is a simplified version of such a check
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'articles_doi'")
                    articles_columns = [row[0] for row in cursor.fetchall()]
                    expected_columns = ['doc_id', 'metadata']
                    if not all(col in articles_columns for col in expected_columns + ['doi']):
                        logger.error("Table structure for articles_doi is incorrect.")
                        raise Exception("Table structure is incorrect.")

            self.switch(True)  # Enable the plugin
            logger.info("DOIHandle plugin setup completed successfully.")
        except Exception as e:
            db_connection.rollback()
            logger.error(f"An error occurred during setup: {e}")
            raise e
    
    def switch(self, enable: bool) -> None:
        """Enable or disable the plugin.

        Args:
            enable (bool): True to enable the plugin, False to disable.

        """
        self.enabled = enable
        action = "enabled" if enable else "disabled"
        self.logger.info(f"DOIHandle enabled: {self.enabled}")
    
    def delete(self) -> None:
        """
        Disable the DOIHandle plugin and clean up any resources it created, 
        such as database tables, webpages, or frontend components.
        """
        if self.enabled:
            self.switch(False)  # Ensure the plugin is disabled before deletion

        db_connection = store.connection
        try:
            with db_connection.cursor() as cursor:
                # Drop the plugin's database tables
                cursor.execute("""
                    DROP TABLE IF EXISTS articles_doi;
                """)
                db_connection.commit()
                logger.info("DOIHandle plugin tables and resources have been deleted.")
        except Exception as e:
            db_connection.rollback()
            logger.error(f"Failed to delete DOIHandle plugin tables: {e}")
            raise e
    