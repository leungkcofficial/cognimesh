import numpy as np
from logger import setup_logger

logger = setup_logger(__name__)

class Intellect:
    def __init__(self):
        # Initialization if needed
        pass

    def calculate_similarity(self, doc_embeddings, query_embedding):
        """
        Calculate similarity between document embeddings and a query embedding.

        Args:
            doc_embeddings (numpy.ndarray): 2D numpy array of document embeddings.
            query_embedding (numpy.ndarray): 1D numpy array of the query embedding.

        Returns:
            list: Similarity scores between each document embedding and the query embedding.
        """
        try:
            doc_norms = np.linalg.norm(doc_embeddings, axis=1)
            query_norm = np.linalg.norm(query_embedding)
            similarities = np.dot(doc_embeddings, query_embedding) / (doc_norms * query_norm)
            return similarities
        except Exception as e:
            logger.error(f"Error calculating similarities: {e}", exc_info=True)
            raise

    def present_findings(self, similarities, threshold=0.8):
        """
        Present the findings in natural language based on similarity scores.

        Args:
            similarities (list): Similarity scores between document embeddings and the query embedding.
            threshold (float): Threshold for considering a document as relevant.

        Returns:
            str: Natural language description of the findings.
        """
        try:
            relevant_docs = [i for i, score in enumerate(similarities) if score > threshold]
            if not relevant_docs:
                return "No relevant documents found."
            else:
                description = f"Found {len(relevant_docs)} relevant documents: " + ", ".join(f"Document {i+1}" for i in relevant_docs)
                logger.info(description)
                return description
        except Exception as e:
            logger.error(f"Error presenting findings: {e}", exc_info=True)
            return "An error occurred while processing the findings."