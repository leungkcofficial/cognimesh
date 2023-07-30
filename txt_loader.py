import os
import argparse
from docx import Document
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
from file_utils import sanitize_filename, open_file, save_file, move_file, delete_file, copy_file, rename_file
from summarizer import summarize
from logger import setup_logger

# Get environment variables
OUTPUT_DIR = os.getenv('OUTPUT_DIR')

# Get logger
logger = setup_logger(__name__)

def load_txt(file_path, summarize_ratio=0.2):
    try:
        logger.info(f"Loading txt file from path: {file_path}")

        # If no output_filename provided, use the original file name
        output_filename = None
        if output_filename is None:
            output_filename = os.path.splitext(os.path.basename(file_path))[0]
            
        # Ask the user to input the new file name
        new_filename = input('Please enter a new file name or press Enter to use the original name: ')
        if new_filename:
            output_filename = new_filename
        
        output_filename = sanitize_filename(output_filename)

        # Rename the txt file with the sanitized file name
        new_file_path = os.path.join(os.path.dirname(file_path), f"{output_filename}.txt")
        rename_file(file_path, new_file_path)

        output_dir = os.getenv('OUTPUT_DIR')
        if not output_dir or not os.path.isdir(output_dir):
            logger.error('Output path invalid.')
            return

        # Summarize the text file
        summarize_prompt_input = open_file(r'prompt/doc_summerize_bot_prompt.txt')
        summary_path = summarize(new_file_path, summarize_prompt_input, summarize_ratio=summarize_ratio)
        
        logger.info(f"Saved summary to {summary_path}")

    except Exception as e:
        logger.error(f"Error loading txt file: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Load a txt file and create a summary.')
    parser.add_argument('file_path', type=str, help='The path to the txt file.')
    parser.add_argument('--ratio', type=float, default=0.2, help='The ratio for the summarizer.')
    
    args = parser.parse_args()

    load_txt(args.file_path, args.ratio)
