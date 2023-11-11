from backend.axon.in_come import File
from backend.neuron.memory import Memory #, Cognition
from backend.neuron.cognition import Cognition
from logger import setup_logger

logger = setup_logger(__name__)

def process_file(path: str,
                 loader_class,
                 chunk_size: int,
                 chunk_overlap: int):
    file = File()
    file.import_path(filepath=path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    memory = Memory()
    
    if file.check_duplicate_in_db():
        # If the file is already processed, retrieve the corresponding doc_id
        doc_id = memory.retrieve_doc_id(file.file_sha1)
        if doc_id:
            logger.info(f"File with SHA1 {file.file_sha1} has already been processed with doc_id {doc_id}.")
            return doc_id
        else:
            logger.error(f"No doc_id found for file with SHA1 {file.file_sha1}.")
            return None
    else:
        # Process the file if it's not a duplicate
        cognition = Cognition()
        embed = cognition.embed_file(file=file, loader_class=loader_class)

        # Add document metadata and vector embeddings to the database
        doc_id = memory.add_document(file=file)
        vector_ids = memory.add_vectors(file=file, embed=embed)
        memory.update_document_vectors(doc_id, vector_ids)
        return doc_id
