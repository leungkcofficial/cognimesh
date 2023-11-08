from backend.axon.in_come import File
from backend.settings.backend_setting import store
from backend.neuron.neuron import Memory, Cognition
from logger import setup_logger


logger = setup_logger(__name__)

def process_file(path: str,
                 loader_class,
                 chunk_size: int,
                 chunk_overlap: int):
    file = File()
    file.import_path(filepath=path,
                     chunk_size=chunk_size,
                     chunk_overlap=chunk_overlap)
    if not file.check_duplicate_in_db():
    # If not, process the file
        cognition = Cognition()
        embed = cognition.create_vector(file=file, loader_class=loader_class)

        # store = PGDocStore()
        memory = Memory()

        # Add document metadata and vector embeddings to the database
        doc_id = memory.add_document(file=file)
        vector_ids = memory.add_vectors(file=file, embed=embed)
        memory.update_document_vectors(doc_id, vector_ids)
    else:
        print(f"File with SHA1 {file.file_sha1} is already processed.")
