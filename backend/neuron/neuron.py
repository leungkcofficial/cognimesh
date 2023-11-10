import os
import uuid
from pydantic import BaseModel
from logger import setup_logger
from typing import List
# Importing from the new module files
from ..settings.storage import store
from ..settings.embedding import embedding
from ..axon.in_come import File

logger = setup_logger(__name__)

class Cognition(BaseModel):
    def create_vector(self, file: File, loader_class):
        file.compute_documents(loader_class)
        embed = embedding.embed_documents([doc.page_content for doc in file.documents])
        return embed


class Memory:
    def __init__(self):
        self.store = store
        
    def add_document(self, file: File):
        cur = self.store.get_cursor()
        try:
            cur.execute("""
                INSERT INTO documents (file_path, file_name, file_size, file_sha1, file_extension, chunk_size, chunk_overlap)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING doc_id
            """, (
                file.file_path,
                file.file_name,
                file.file_size,
                file.file_sha1,
                file.file_extension,
                file.chunk_size,
                file.chunk_overlap
            ))
            file.doc_id = cur.fetchone()[0]
            self.store.commit()
        except Exception as e:
            self.store.rollback()
            raise e
        finally:
            cur.close()
        return file.doc_id

    def add_vectors(self, file: File, embed: List):
        cur = self.store.get_cursor()
        vector_ids = []
        try:
            for vector_index, vector_data in enumerate(embed):
                vector_id = uuid.uuid4()
                vector_ids.append(vector_id)
                cur.execute("""
                    INSERT INTO vectors (vector_id, doc_id, vector_index, embeddings, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    vector_id,
                    file.doc_id,
                    vector_index,
                    vector_data
                ))
            self.store.commit()
        except Exception as e:
            self.store.rollback()
            raise e
        finally:
            cur.close()
        return vector_ids

    def update_document_vectors(self, doc_id, vector_ids: List[uuid.UUID]):
        cur = self.store.get_cursor()
        try:
            # Execute the SQL command, passing the list of UUIDs directly
            cur.execute("""
                UPDATE documents SET vectors_ids = %s WHERE doc_id = %s
            """, (vector_ids, doc_id))
            self.store.commit()
        except Exception as e:
            self.store.rollback()
            raise e
        finally:
            cur.close()

    def retrieval(self, query_embedding, match_threshold=0.8, match_count=5):
        """
        Perform a similarity search in the database using the given query embeddings.

        This method acts as a wrapper to the similarity search functionality in the database,
        handling the interaction and returning the search results.

        Args:
            query_embedding (list): The embedding vector of the query document.
            match_threshold (float): The threshold for matching similarity. Defaults to 0.8.
            match_count (int): The number of matches to return. Defaults to 5.

        Returns:
            list: A list of tuples containing matched document IDs, content, and similarity scores.

        Raises:
            Exception: If an error occurs during the database interaction or the search process.
        """
        try:
            matches = self.store.similarity_search(query_embedding, match_threshold, match_count)
            logger.info(f"Retrieved {len(matches)} matches for the given query.")
            return matches
        except Exception as e:
            logger.error(f"An error occurred during the retrieval process: {e}")
            raise e

        