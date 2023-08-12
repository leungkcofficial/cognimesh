import os
import argparse
from docx import Document
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
from file_utils import sanitize_filename, open_file, save_file, move_file, delete_file, copy_file, rename_file
from summarizer import summarize
from logger import setup_logger

# Create a logger for this module
logger = setup_logger(__name__)

# Get environment variables
output_dir = os.getenv('OUTPUT_DIR')
if not output_dir or not os.path.isdir(output_dir):
    logger.error('Output path invalid.')

def load_docx(file_path, summarize_ratio=0.2):
    try:
        logger.info(f"Loading docx file from path: {file_path}")

        # Read docx file
        document = Document(file_path)
        text_content = '\n'.join([para.text for para in document.paragraphs])

        # Save the content to a text file
        docx_filename = os.path.basename(file_path)
        filename, _ = os.path.splitext(docx_filename)
        sanitized_filename = sanitize_filename(filename)
        txt_file_path = os.path.join(output_dir, f"{sanitized_filename}.txt") # type: ignore
        save_file(txt_file_path, text_content)

        logger.info(f"Saved text content to {txt_file_path}")

        # Summarize the document
        summarize_prompt_input = open_file(r'prompt/doc_summerize_bot_prompt.txt')
        summary_path = summarize(txt_file_path, summarize_prompt_input, summarize_ratio=summarize_ratio)
        
        logger.info(f"Saved summary to {summary_path}")

    except Exception as e:
        logger.error(f"Error loading docx file: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Load a docx file and create a summary.')
    parser.add_argument('file_path', type=str, help='The path to the docx file.')
    parser.add_argument('--ratio', type=float, default=0.2, help='The ratio for the summarizer.')
    
    args = parser.parse_args()

    load_docx(args.file_path, args.ratio)