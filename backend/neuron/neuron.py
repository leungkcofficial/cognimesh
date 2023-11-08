import os
import uuid
from pydantic import BaseModel
from langchain.embeddings.openai import OpenAIEmbeddings
from logger import setup_logger
from typing import List
from ..settings.backend_setting import Setting, store
from ..axon.in_come import File

logger = setup_logger(__name__)
# Read local .env file

class Cognition(BaseModel):
    def create_vector(self, file: File, loader_class) -> OpenAIEmbeddings:
        file.compute_documents(loader_class)
        setting = Setting()
        api_key = setting.openai_api_key
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        embed = embeddings.embed_documents([doc.page_content for doc in file.documents])
        return embed

    # def duplicate_file_exist(self, file: File):

class Memory:
    def __init__(self):
        self.doc_store = store
        
    def add_document(self, file: File):
        cur = self.doc_store.get_cursor()
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
            self.doc_store.commit()
        except Exception as e:
            self.doc_store.rollback()
            raise e
        finally:
            cur.close()
        return file.doc_id

    def add_vectors(self, file: File, embed: List):
        cur = self.doc_store.get_cursor()
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
            self.doc_store.commit()
        except Exception as e:
            self.doc_store.rollback()
            raise e
        finally:
            cur.close()
        return vector_ids

    def update_document_vectors(self, doc_id, vector_ids: List[uuid.UUID]):
        cur = self.doc_store.get_cursor()
        try:
            # Execute the SQL command, passing the list of UUIDs directly
            cur.execute("""
                UPDATE documents SET vectors_ids = %s WHERE doc_id = %s
            """, (vector_ids, doc_id))
            self.doc_store.commit()
        except Exception as e:
            self.doc_store.rollback()
            raise e
        finally:
            cur.close()

    

        