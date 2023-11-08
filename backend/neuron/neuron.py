import os
import uuid
from pydantic import BaseModel
from langchain.embeddings.openai import OpenAIEmbeddings
from logger import setup_logger
from ..settings.backend_setting import Setting, PGDocStore
from ..axon.in_come import File

logger = setup_logger(__name__)
# Read local .env file

class Memory(BaseModel):
    def create_vector(self, file: File, loader_class) -> OpenAIEmbeddings:
        file.compute_documents(loader_class)
        setting = Setting()
        api_key = setting.openai_api_key
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        embed = embeddings.embed_documents([doc.page_content for doc in file.documents])
        return embed

    # def duplicate_file_exist(self, file: File):

# class DocStore:
    

        