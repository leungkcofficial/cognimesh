import uuid
from typing import List
from logger import setup_logger
import numpy as np
from ..settings.storage import store
from ..axon.in_come import File

logger = setup_logger(__name__)

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

    def update_file_content(self, doc_id, file_content):
        """
        Updates the file_content of a document in the database.

        Args:
            doc_id (UUID): The unique identifier of the document.
            file_content (str): The text content to be saved in the file_content column.
        """
        cur = self.store.get_cursor()
        try:
            cur.execute("""
                UPDATE documents SET content = %s WHERE doc_id = %s
            """, (file_content, doc_id))
            self.store.commit()
        except Exception as e:
            self.store.rollback()
            raise e
        finally:
            cur.close()
    
    def retrieve_doc_id(self, sha1):
        """
        Retrieves the document ID for a given SHA-1 hash value.

        Args:
            sha1 (str): The SHA-1 hash value of the document.

        Returns:
            UUID: The unique identifier of the document if found, otherwise None.
        """
        try:
            doc_id = self.store.retrieve_doc_id(sha1)
            if doc_id:
                return doc_id
            else:
                logger.info(f"No document found for SHA-1 hash {sha1}")
                return None
        except Exception as e:
            logger.error(f"An error occurred while retrieving the document ID for SHA-1 hash {sha1}: {e}")
            return None
    
    def retrieve_embeddings(self, doc_id):
        """
        Retrieves all embeddings for a given document ID and converts them to a 2D numpy array.

        Args:
            doc_id (UUID): The unique identifier of the document.

        Returns:
            numpy.ndarray: 2D numpy array of embeddings.
        """
        embedding_strings = self.store.retrieve_embeddings(doc_id)
        embedding_arrays = [np.array(embed_str.strip('[]').split(','), dtype=float) for embed_str in embedding_strings]
        return np.vstack(embedding_arrays)
    
    def retrieve_file(self, doc_id):
        """
        Retrieves the file metadata for a given document ID.

        Args:
            doc_id (UUID): The unique identifier of the document.

        Returns:
            dict: A dictionary containing file metadata like file_path and file_extension.
        """
        try:
            chunks_metadata = self.store.retrieve_chunks(doc_id)
            file_path = chunks_metadata['file_path']
            chunk_size = chunks_metadata['chunk_size']
            chunk_overlap = chunks_metadata['chunk_overlap']
            if file_path:
                file = File()
                file.import_path(filepath=file_path,
                                 chunk_size=chunk_size,
                                 chunk_overlap=chunk_overlap)
                return file
            else:
                logger.error(f"No file found for doc_id {doc_id}")
                return None
        except Exception as e:
            logger.error(f"An error occurred while retrieving the file for doc_id {doc_id}: {e}")
            return None
    
    def retrieve_chunk(self, doc_id, chunk_index, loader_class):
        """
        Retrieve and return a specific chunk from a document using its doc_id.

        Args:
            doc_id (UUID): The unique identifier of the document.
            chunk_index (int): The index of the chunk to retrieve.
            loader_class (class): The class of the loader to use to load the file.

        Returns:
            str: The text of the specified chunk.
        """
        # Retrieve metadata from PGDocStore
        chunks_metadata = self.store.retrieve_chunks(doc_id)
        file_path = chunks_metadata['file_path']
        chunk_size = chunks_metadata['chunk_size']
        chunk_overlap = chunks_metadata['chunk_overlap']

        # Use the File class to recreate the chunks
        file_processor = File(
            file_path=file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        file_processor.import_path(file_path, chunk_size, chunk_overlap)
        file_processor.compute_documents(loader_class)

        # Extract and return the specific chunk
        if chunk_index < 0 or chunk_index >= len(file_processor.documents):
            raise IndexError(f"Chunk index {chunk_index} is out of range for document {doc_id}")

        return file_processor.documents[chunk_index]
    
    def retrieval_in_document(self, query_embedding, doc_id, match_threshold=0.8, match_count=5):
        """
        Perform a similarity search for the given query embeddings within a specific document.

        Args:
            query_embedding (list): The embedding vector of the query.
            doc_id (UUID): The unique identifier of the document to search within.
            match_threshold (float): The threshold for matching similarity. Defaults to 0.8.
            match_count (int): The number of matches to return. Defaults to 5.

        Returns:
            list: A list of tuples containing matched content and similarity scores within the specified document.

        Raises:
            Exception: If an error occurs during the database interaction or the search process.
        """
        try:
            # Retrieve embeddings for the specified document
            document_embeddings = self.store.retrieve_document_embeddings(doc_id)

            # Perform similarity search with the query embedding against these document embeddings
            matches = self.perform_similarity_search(query_embedding, document_embeddings, match_threshold, match_count)
            
            logger.info(f"Retrieved {len(matches)} matches for the given query in document {doc_id}.")
            return matches
        except Exception as e:
            logger.error(f"An error occurred during the retrieval process in document {doc_id}: {e}")
            raise e

        