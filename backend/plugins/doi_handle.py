from ..settings.plugin import PluginInterface
from ..settings.storage import store # Import store to access the database connection
from ..axon.file_utils import sanitize_filename, open_file, save_file, move_file, delete_file, copy_file, rename_file
import asyncio
from ..neuron.brain import Brain
from ..neuron.memory import Memory
from typing import Any, Optional, List
from logger import setup_logger
import os
import json
import requests

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
    
    def verify_doi(self, doi):
        """
        Verifies a DOI by attempting to retrieve metadata from CrossRef.

        Args:
            doi (str): The DOI to verify.

        Returns:
            bool: True if the DOI is valid and metadata can be retrieved, False otherwise.
        """
        crossref_url = f"https://api.crossref.org/works/{doi}"
        try:
            response = requests.get(crossref_url)
            if response.status_code == 200:
                logger.info(f"Metadata retrieved for DOI {doi}")
                return True
            else:
                logger.warning(f"Unable to retrieve metadata for DOI {doi}")
                return False
        except Exception as e:
            logger.error(f"Error verifying DOI {doi}: {e}")
            return False
    
    async def retrieve_doi(self, doc_id):
        """
        Retrieves the DOI from the text content of a document.

        Args:
            doc_id (UUID): The unique identifier of the document.

        Returns:
            str: The detected DOI or None if not found.
        """
        memory = Memory()
        brain = Brain()

        try:
            file_content = memory.retrieve_content(doc_id)
            if file_content:
                prompt = file_content[:10000]  # Truncate to avoid overload
                custom_instructions = open_file(r'prompt/citation_bot_prompt.txt')
                full_prompt = f"{custom_instructions}\n{prompt}"

                # Make sure to call the query_async function correctly
                response = await brain.query_async(model="gpt-4-1106-preview", 
                                                   prompt=full_prompt, 
                                                   is_chat_model=True, 
                                                   temperature=0.7, 
                                                   max_tokens=1000)

                if response:
                    doi = response['choices'][0]['message']['content'] # Logic to extract DOI from response
                    if doi != "No DOI available, caution for citation." and self.verify_doi(doi):
                        try:
                            with store.connection.cursor() as cursor:
                                cursor.execute("""
                                    INSERT INTO articles_doi (doc_id, doi)
                                    VALUES (%s, %s)
                                    ON CONFLICT (doc_id) DO UPDATE 
                                    SET doi = EXCLUDED.doi;
                                """, (doc_id, doi))
                                store.connection.commit()
                                logger.info(f"Verified DOI {doi} saved for doc_id {doc_id}")
                        except Exception as e:
                            store.connection.rollback()
                            logger.error(f"Error saving DOI for doc_id {doc_id}: {e}")
                    else:
                        logger.info("No valid DOI found to save.")
            else:
                logger.warning(f"No content found for doc_id {doc_id}")
            return None
        except Exception as e:
            logger.error(f"Error in retrieve_doi for doc_id {doc_id}: {e}")
            return None
    
    def retrieve_metadata(self, doi):
        """
        Retrieves and stores metadata for a given DOI from CrossRef.

        Args:
            doi (str): The DOI for which to retrieve metadata.

        Returns:
            bool: True if metadata is successfully retrieved and saved, False otherwise.
        """
        if self.verify_doi(doi):
            crossref_url = f"https://api.crossref.org/works/{doi}"
            try:
                response = requests.get(crossref_url)
                if response.status_code == 200:
                    metadata = response.json()
                    with store.connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE articles_doi SET metadata = %s WHERE doi = %s;
                        """, (json.dumps(metadata), doi))
                        store.connection.commit()
                        logger.info(f"Metadata for DOI {doi} saved successfully.")
                        return True
                else:
                    logger.warning(f"Unable to retrieve metadata for DOI {doi}. Status Code: {response.status_code}")
                    return False
            except Exception as e:
                store.connection.rollback()
                logger.error(f"Error retrieving metadata for DOI {doi}: {e}")
                return False
        else:
            logger.warning(f"Verification failed for DOI {doi}.")
            return False
        
    async def process_new_document(self, doc_id):
        """
        Processes a new document by retrieving its DOI and metadata.

        Args:
            doc_id (UUID): The unique identifier of the new document.

        """
        try:
            if not self.retrieve_doi(doc_id):
                logger.info(f"No DOI found or failed to retrieve for doc_id {doc_id}.")
                return

            if not self.retrieve_metadata(doc_id):
                logger.info(f"Failed to retrieve metadata for DOI associated with doc_id {doc_id}.")
                return

            logger.info(f"Metadata stored successfully for doc_id {doc_id}.")
        except Exception as e:
            logger.error(f"Error processing new document with doc_id {doc_id}: {e}")
        finally:
            store.close_connection()