from ..settings.backend_setting import store
from ..settings.plugin import PluginInterface

class ZoteroConnect(PluginInterface):
    
    # ... other methods ...

    def setup_database(self, db_connection):
        # Use the db_connection to create a new table
        db_connection = store.get_connection()
        cursor = db_connection.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zotero_articles (
                    id SERIAL PRIMARY KEY,
                    doc_id UUID NOT NULL,
                    doi VARCHAR(255),
                    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
                );
                CREATE TABLE IF NOT EXISTS zotero_books (
                    id SERIAL PRIMARY KEY,
                    doc_id UUID NOT NULL,
                    isbn VARCHAR(255),
                    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
                );
            """)
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            # Handle exceptions, possibly logging them or re-raising
            raise
        finally:
            cursor.close()