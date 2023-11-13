import uuid
from typing import List
from logger import setup_logger
from ..settings.storage import store
from ..axon.in_come import File

logger = setup_logger(__name__)

class Memory:
    def __init__(self):
        self.store = store

    def _execute_db_command(self, query, params):
        """
        Executes a database command with the provided query and parameters,
        handling transactions and cursor management.
        """
        with self.store.get_cursor() as cur:
            try:
                cur.execute(query, params)
                self.store.commit()
                return cur.fetchone() if 'RETURNING' in query else None
            except Exception as e:
                self.store.rollback()
                logger.error(f"Database command execution failed: {e}")
                return None
        
    def check_duplicate_in_db(self, file: File):
        """
        Check if a file with the same SHA1 hash already exists in the database.
        Args:
            file (File): The file object to check for duplicates.
        Returns:
            bool: True if a duplicate exists, False otherwise.
        """
        try:
            with self.store.get_cursor() as cur:
                cur.execute("SELECT doc_id FROM documents WHERE file_sha1 = %s", (file.file_sha1,))
                duplicate = cur.fetchone()
                return duplicate is not None
        except Exception as e:
            logger.error(f"Error checking for duplicate: {e}")
            return False
    
    def add_document(self, file: File):
        return self._execute_db_command("""
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

    def add_vectors(self, file: File, embed: List):
        vector_ids = [uuid.uuid4() for _ in embed]
        for vector_id, vector_data in zip(vector_ids, embed):
            self._execute_db_command("""
                INSERT INTO vectors (vector_id, doc_id, vector_index, embeddings, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                vector_id,
                file.doc_id,
                vector_data
            ))
        return vector_ids

    def update_document_vectors(self, doc_id, vector_ids: List[uuid.UUID]):
        self._execute_db_command("""
            UPDATE documents SET vectors_ids = %s WHERE doc_id = %s
        """, (vector_ids, doc_id))

    def update_file_content(self, doc_id, file_content):
        self._execute_db_command("""
            UPDATE documents SET content = %s WHERE doc_id = %s
        """, (file_content, doc_id))
    
    def retrieve_doc_id(self, sha1):
        try:
            doc_id = self.store.retrieve_doc_id(sha1)
            if doc_id:
                return doc_id
            else:
                logger.info(f"No document found for SHA-1 hash {sha1}")
        except Exception as e:
            logger.error(f"An error occurred while retrieving the document ID for SHA-1 hash {sha1}: {e}")

    def retrieve_embeddings(self, doc_id):
        # Assuming store.retrieve_embeddings returns a list of embedding strings
        embedding_strings = self.store.retrieve_embeddings(doc_id)
        return [np.array(embed_str.strip('[]').split(','), dtype=float) for embed_str in embedding_strings]

    def retrieve_file(self, doc_id):
        try:
            chunks_metadata = self.store.retrieve_chunks(doc_id)
            if chunks_metadata:
                file = File()
                file.import_path(filepath=chunks_metadata['file_path'],
                                 chunk_size=chunks_metadata['chunk_size'],
                                 chunk_overlap=chunks_metadata['chunk_overlap'])
                return file
            else:
                logger.error(f"No file found for doc_id {doc_id}")
        except Exception as e:
            logger.error(f"An error occurred while retrieving the file for doc_id {doc_id}: {e}")
    
    def retrieve_content(self, doc_id):
        try:
            content = self.store.retrieve_content(doc_id)
            if content is not None:
                logger.info(f"Content retrieved for doc_id {doc_id}")
                return content
            else:
                logger.warning(f"No content found for doc_id {doc_id}")
        except Exception as e:
            logger.error(f"Error retrieving content for doc_id {doc_id}: {e}")
    
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

        