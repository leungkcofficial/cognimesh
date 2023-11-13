import os
from typing import Optional, List, Any
from fastapi import UploadFile
from pydantic import BaseModel, Field
from uuid import UUID
from ..settings.file_utils import get_file_size, compute_sha1_from_file
from logger import setup_logger

logger = setup_logger(__name__)

class File(BaseModel):
    file: Optional[UploadFile]
    file_name: Optional[str] = ""
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_sha1: Optional[str] = ""
    vectors_ids: List[UUID] = Field(default_factory=list)
    doc_id: UUID = Field(default=None)
    file_extension: Optional[str] = ""
    content: Optional[Any] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    documents: Optional[Any] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def import_path(self, filepath: str, chunk_size: int = 500, chunk_overlap: int = 50):
        # Existing logic for importing the file path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a valid file.")
        self.file_path = filepath
        self.file_name = os.path.basename(filepath)
        self.file_extension = os.path.splitext(self.file_name)[-1].lower()
        with open(filepath, 'rb') as f:
            self.content = f.read()
        self.file_size = get_file_size(filepath)
        self.file_sha1 = compute_sha1_from_file(filepath)

    def process_file(self, loader_class, store):
        self.import_path(self.file_path)
        if self.check_duplicate_in_db(store):
            logger.info(f"Duplicate file detected with SHA1 {self.file_sha1}. Skipping upload and embedding.")
            return
        logger.info(f"No duplicate found for SHA1 {self.file_sha1}. Proceeding with upload and embedding.")
        self.compute_documents(loader_class)
            
    def compute_documents(self, loader_class):
        try:
            # Assuming loader_class can take a bytes-like object directly
            loader = loader_class(self.content)
            documents = loader.load()

            # Optimize the splitting process
            # Assuming RecursiveCharacterTextSplitter can take a stream or iterator
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )
            self.documents = text_splitter.split_documents(documents)

        except Exception as e:
            logger.error(f"Error in computing documents: {e}")
            # Handle or raise the exception as per your application's needs

    

