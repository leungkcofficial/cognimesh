from pydantic import BaseModel
from logger import setup_logger
# Importing from the new module files
from ..settings.embedding import embedding
from ..axon.in_come import File

logger = setup_logger(__name__)

class Cognition(BaseModel):
    def embed_file(self, file: File, loader_class):
        file.compute_documents(loader_class)
        embed = embedding.embed_documents([doc.page_content for doc in file.documents])
        return embed
    
    def embed_text(self, text: str):
        """
        Embeds the given text (query or any string input) using the same embedding model as for documents.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector for the text.
        """
        text_embedding = embedding.embed_documents([text])[0]
        return text_embedding  # Assuming embed_text returns a list of embeddings