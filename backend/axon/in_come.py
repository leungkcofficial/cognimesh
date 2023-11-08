import tempfile
from typing import Any, Optional, List
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from logger import setup_logger
import os
from pydantic import BaseModel, Field
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
                # # Set vectors_ids attribute
                # self.vectors_ids = vector_id_from_sha1(self.file_sha1)
                os.remove(tmp_file.name)  
            
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
    
    # def set_file_name(self, name: str):
    #     self.file_name = name
    
    # def file_is_empty(self):
    #     """
    #     Check if file is empty by checking if the file pointer is at the beginning of the file
    #     """
    #     return self.file.size < 1  # pyright: ignore reportPrivateUsage=none
    
      
    # def add_file_to_db(self):
    #     load_dotenv(find_dotenv())
    #     host= os.getenv('PG_HOST')
    #     port= os.getenv('PG_PORT')
    #     user= os.getenv('PG_USER')
    #     password= os.getenv('PG_PASS')
    #     dbname= 'cognimesh'

    #     CONNECTION_STRING = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?client_encoding=utf8"
    
    #     # Set up engine and session
    #     engine = create_engine(CONNECTION_STRING)
    #     Session = sessionmaker(bind=engine)
        
    #     try:
    #         sql = """
    #                 INSERT INTO documents (file_name, file_size, file_sha1, file_extension, content)
    #                 VALUES (:file_name, :file_size, :file_sha1, :file_extension, :content);
    #             """
    #         params = {"file_name": self.file_name,
    #                 "file_size": self.file_size,
    #                 "file_sha1": self.file_sha1,
    #                 "file_extension": self.file_extension,
    #                 "content": self.content
    #                 }
    #         Session.execute(sql, params)
    #                 # Commit the changes to the database
    #         Session.commit()

    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #         Session.rollback()  # Rollback any changes in case of error
    #     finally:
    #         Session.close()  # Close the session
