
from .settings import Setting
from langchain.embeddings.openai import OpenAIEmbeddings
import openai
import logging
from logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingService:
    def __init__(self, setting: Setting):
        self.setting = setting
        if self.setting.embedding_model == 'openai':
            self.embedder = OpenAIEmbeddings(openai_api_key=self.setting.openai_api_key)
        # Add other models here
        else:
            logger.error(f"Unsupported embedding model: {self.setting.embedding_model}")
            raise NotImplementedError(f"Embedding model {self.setting.embedding_model} is not implemented")

    def embed_documents(self, documents):
        """
        Embeds the given documents using the selected embedding model.

        Args:
            documents (List[str]): A list of document texts to be embedded.

        Returns:
            List: A list of embedding vectors for the provided documents.

        Raises:
            Exception: If an error occurs during the embedding process.
        """
        try:
            return self.embedder.embed_documents(documents)
        except Exception as e:
            logger.error(f"Error during document embedding: {e}")
            raise e

# Global embedding instance
setting = Setting()
try:
    embedding = EmbeddingService(setting)
except Exception as e:
    logging.error(f"Error initializing EmbeddingService: {e}")
    raise e