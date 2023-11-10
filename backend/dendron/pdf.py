from backend.axon.in_come import File
from backend.neuron.memory import Memory #, Cognition
from backend.neuron.cognition import Cognition
from backend.dendron.out_go import process_file
import io
from langchain.document_loaders import PDFPlumberLoader
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from logger import setup_logger

logger = setup_logger(__name__)


def retrieve_and_verify_pdf(doc_id):
    memory = Memory()
    file_data = memory.retrieve_file(doc_id)

    if file_data:
        file_path = file_data.file_path
        file_extension = file_data.file_extension

        # Verify if the file is a PDF
        if file_extension.lower() == '.pdf':
            # Check if the file exists at the file_path
            try:
                with open(file_path, 'rb') as f:
                    # File is successfully opened, proceed with further processing
                    print(f"PDF file located: {file_path}")
                    # Further processing code goes here
                    return file_data
            except FileNotFoundError:
                print(f"File not found at {file_path}")
        else:
            print(f"The file with doc_id {doc_id} is not a PDF.")
    else:
        print(f"No file data found for doc_id {doc_id}")
        
def convert_pdf_to_txt(file_content, ocr_threshold=0.8):
    text = ''
    text_pages = 0
    try:
        # Using BytesIO to handle the file content as a stream
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                    text_pages += 1

            # Use OCR if the text extraction is insufficient
            if text_pages < len(pdf.pages) * ocr_threshold:
                text = ''
                images = convert_from_bytes(file_content, dpi=300)
                for img in images:
                    text += pytesseract.image_to_string(img)
    except Exception as e:
        print(f"Error occurred while converting PDF to text: {e}")
    return text

def process_pdf(file_path: str,
                chunk_size: int,
                chunk_overlap: int,
                loader_class=PDFPlumberLoader):
    # Process the file and get doc_id
    doc_id = process_file(file_path, loader_class, chunk_size, chunk_overlap)

    if doc_id:
        # Convert PDF to text
        file = retrieve_and_verify_pdf(doc_id)
        pdf_text = convert_pdf_to_txt(file.content)

        # Update the content in the database
        memory = Memory()
        memory.update_file_content(doc_id, pdf_text)

        print("PDF processing completed and content updated in database.")
    else:
        print("Error in processing PDF file.")