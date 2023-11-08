import tempfile
from typing import Any, Optional, List
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from logger import setup_logger
import os
from pydantic import BaseModel, Field
from ..settings.backend_setting import PGDocStore, store
from uuid import UUID
from file_utils import open_file, get_file_size, compute_sha1_from_file, sanitize_filename, vector_id_from_sha1

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

    def import_path(self, 
                    filepath: str,
                    chunk_size: int,
                    chunk_overlap: int):
        if not os.path.isfile(filepath):
            raise ValueError(f"{filepath} is not a valid file.")

        if filepath:
            # Ensure the file exists
            if not os.path.exists(filepath):
                raise ValueError(f"File not found: {filepath}")
            # Set file_name attribute
            self.file_name = os.path.basename(filepath)
            # Set file_path attribute
            self.file_path = filepath
            # Set file_extension attribute
            self.file_extension = os.path.splitext(self.file_name)[-1].lower()
            # Set chunk_size attribute
            self.chunk_size = chunk_size
            # Set chunk_overlap attribute
            self.chunk_overlap = chunk_overlap

            # Read the file content and set content attribut
            with tempfile.NamedTemporaryFile(delete=False,
                                    suffix=self.file_name,  # pyright: ignore reportPrivateUsage=none
                                    ) as tmp_file:
                with open(self.file_path, 'rb') as f:
                    f.seek(0)  # pyright: ignore reportPrivateUsage=none
                    self.content = f.read()  # pyright: ignore reportPrivateUsage=none
                tmp_file.write(self.content)
                tmp_file.flush()
                # Set file_size attribute
                self.file_size = get_file_size(tmp_file.name)
                # Set file_sha1 attribute
                self.file_sha1 = compute_sha1_from_file(tmp_file.name)
                os.remove(tmp_file.name)  
            
    def check_duplicate_in_db(self):
        """
        Check if a file with the same SHA1 hash already exists in the database.

        Returns:
            bool: True if a duplicate exists, False otherwise.
        """
        # pg_store = PGDocStore()  # Initialize your database connection handler
        cur = None  # Initialize cur to None
        try:
            cur = store.get_cursor()
            cur.execute("SELECT doc_id FROM documents WHERE file_sha1 = %s", (self.file_sha1,))
            duplicate = cur.fetchone()
            return duplicate is not None
        except Exception as e:
            logger.error(f"Error checking for duplicate: {e}")
            return False
        finally:
            cur.close()  # Ensure the connection is closed after checking
            
    def process_file(self, loader_class):
        """
        Process the file: check for duplicates, upload, and embed if necessary.

        Args:
            loader_class (class): The class of the loader to use to load the file
        """
        self.import_path(self.file_path, self.chunk_size, self.chunk_overlap)
        self.compute_sha1()

        if self.check_duplicate_in_db():
            logger.info(f"Duplicate file detected with SHA1 {self.file_sha1}. Skipping upload and embedding.")
            return

        logger.info(f"No duplicate found for SHA1 {self.file_sha1}. Proceeding with upload and embedding.")
        self.compute_documents(loader_class)
            
    def compute_documents(self, loader_class):
        """
        Compute the documents from the file

        Args:
            loader_class (class): The class of the loader to use to load the file
        """

        documents = []
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=self.file_name,  # pyright: ignore reportPrivateUsage=none
        ) as tmp_file:
            tmp_file.write(self.content)  # pyright: ignore reportPrivateUsage=none
            tmp_file.flush()
            loader = loader_class(tmp_file.name)
            documents = loader.load()

        os.remove(tmp_file.name)

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )

        self.documents = text_splitter.split_documents(documents)
    

