from logger import setup_logger
from ..axon.in_come import File
from ..neuron.neuron import Memory
from ..settings.backend_setting import PGDocStore


logger = setup_logger(__name__)

def process_file(path: str,
                 loader_class,
                 chunk_size: int,
                 chunk_overlap: int):
    file = File()
    file.import_path(filepath=path,
                     chunk_size=chunk_size,
                     chunk_overlap=chunk_overlap)
    mem_neuron = Memory()
    embed = mem_neuron.create_vector(file = file, 
                                     loader_class=loader_class)
    doc_store = PGDocStore()
    doc_store.add_document(file=file)
    # cur.execute("""
    #     INSERT INTO vector (doc_id, embeddings) VALUES (%s, %s)
    # """, (doc_id, vector.tolist()))
    # return file