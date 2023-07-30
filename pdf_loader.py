import os
import re
import argparse
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

from file_utils import sanitize_filename, open_file, save_file, move_file, delete_file, copy_file, rename_file
from summarizer import summarize
from zotero_hook import add_item_by_doi
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

# Import setup_logger from logger.py
from logger import setup_logger
from gpt2brain import OpenAIBrain

# Initialize the GPT-3 brain
brain = OpenAIBrain()

# Initialize the logger
logger = setup_logger('pdf_loader')

def convert_pdf_to_txt(path, ocr_threshold=0.8):
    text = ''
    text_pages = 0
    try:
        logger.info(f"Converting PDF to text from path: {path}")
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:  # Not all pages will return text
                    text += page_text
                    text_pages += 1
            # If the count of non-empty page_text is less than the number of pages
            # convert the PDF to images and perform OCR
            if text_pages < len(pdf.pages) * ocr_threshold:
                text = ''
                images = convert_from_path(path, dpi=300)
                for img in images:
                    text += pytesseract.image_to_string(img)
    except Exception as e:
        logger.error(f"Error occurred while converting PDF to text: {e}")
    return text

def extract_doi_from_text(text):
    try:
        logger.info(f"Extracting DOI from text")
        pattern = re.compile(r'\\b(10[.][0-9]{4,}(?:[.][0-9]+)*/\\S+)\\b')
        match = pattern.search(text)
        print(match)
        if match:
            doi = match.group()
            # Remove any characters after the last digit
            cleaned_doi = re.sub(r'(?<=\\d)\\D+$', '', doi)
            return cleaned_doi
        return None
    except Exception as e:
        logger.error(f"Error extracting DOI from text: {e}")

def validate_pdf(file_path):
    """
    Checks if the given file is a PDF.

    Parameters:
    file_path (str): Path to the file.

    Returns:
    bool: True if the file is a PDF, False otherwise.
    """
    try:
        logger.info(f"Validating if file is a PDF")
        if not file_path.endswith('.pdf'):
            logger.warning('The file is not a PDF.')
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating PDF file: {e}")

def ensure_output_directory_exists(output_directory='output'):
    """
    Creates an output directory in the current working directory, if it doesn't exist.

    Returns:
    str: Path to the output directory.
    """
    try:
        logger.info(f"Ensuring output directory exists: {output_directory}")
        output_directory = os.path.join(os.getcwd(), output_directory)
        os.makedirs(output_directory, exist_ok=True)
        return output_directory
    except Exception as e:
        logger.error(f"Error ensuring output directory exists: {e}")

def handle_doi(doi):
    """
    Tries to add the DOI to Zotero and returns the sanitized filename if successful.

    Parameters:
    doi (str): The DOI to be added to Zotero.

    Returns:
    str: The sanitized filename if successful, None otherwise.
    """
    if doi is not None:
        try:
            logger.info(f"Handling DOI: {doi}")
            zotero_item = add_item_by_doi(doi)
            citekey = zotero_item
            sanitized_filename = sanitize_filename(citekey)
            return sanitized_filename
        except Exception as e:
            logger.error(f"Failed to add item to Zotero by DOI. Error: {e}")
            return None
    return None

def handle_no_doi():
    """
    Prompts the user for a DOI or filename if no DOI was found.

    Returns:
    str: The sanitized filename if provided by the user, None otherwise.
    """
    doi = input('No DOI retrieved. Please manually enter a DOI or press Enter to skip: ')
    if doi != '':
        try:
            logger.info(f"Handling DOI: {doi}")
            zotero_item = add_item_by_doi(doi)
            citekey = zotero_item
            sanitized_filename = sanitize_filename(citekey)
            return sanitized_filename
        except Exception as e:
            logger.error(f"Failed to add item to Zotero by DOI. Error: {e}")
            return None
    else:
        file_name = input('Please enter a file name or press Enter to use the original name: ')
        if file_name != '':
            sanitized_filename = sanitize_filename(file_name)
            return sanitized_filename
    return None

def save_text_to_file(text_content, sanitized_filename, output_directory):
    """
    Writes the extracted text to a .txt file.

    Parameters:
    text_content (str): The text to be written to the file.
    sanitized_filename (str): The filename to use for the new file.
    output_directory (str): The directory in which to save the file.

    Returns:
    str: The path to the new text file.
    """
    try:
        logger.info(f"Saving text to file")
        txt_file_path = os.path.join(output_directory, f"{sanitized_filename}.txt")
        with open(txt_file_path, 'w') as txt_file:
            txt_file.write(text_content)
        logger.info(f"Saved text content to {txt_file_path}")
        return txt_file_path
    except Exception as e:
        logger.error(f"Error saving text to file: {e}")

def load_pdf(file_path, output_directory='output', filename=None, summarize_ratio=0.2):
    """
    Loads a PDF file, extracts the text, finds and handles DOIs, and saves the text to a new file.

    Parameters:
    file_path (str): Path to the PDF file.

    Returns:
    None
    """
    filename = filename if filename else 'default'  # Assign a default value to filename if it's None
    sanitized_filename = filename  # Assign the default filename to sanitized_filename
    
    try:
        logger.info(f"Loading PDF file from path: {file_path}")
        
        if not validate_pdf(file_path):
            return

        output_directory = ensure_output_directory_exists(output_directory)
        text_content = convert_pdf_to_txt(file_path)

        # Try to extract DOI from text content
        doi = extract_doi_from_text(text_content)
        if doi:
            logger.info(f'DOI scraped: {doi}') 
            sanitized_filename = handle_doi(doi)
            if sanitized_filename is None:  # If DOI is invalid
                doi = input('Invalid DOI. Please manually enter a DOI or press Enter to skip: ')
                if doi:
                    sanitized_filename = handle_doi(doi)
        else:  # If no DOI is scraped
            logger.info('No DOI scraped.')
            # Use GPT-3 to scrape DOI
            doi_bot_prompt = open_file(r'prompt/citation_bot_prompt.txt')
            scrape_prompt = "Extract the DOI from the following text: " + text_content[:10000]  # Limit to first 5000 characters
            scrape_response = brain.generate_response(prompt_input=doi_bot_prompt,
                                                      user_input=scrape_prompt, 
                                                      model="gpt-3.5-turbo-16k")
            print(scrape_response)
            doi = scrape_response.strip()
            # doi = extract_doi_from_text(scrape_response)#['choices'][0]['text'])

            # Check if the DOI is not empty after stripping
            if not doi:
                doi = input('Please manually enter a DOI or press Enter to skip: ')

            # Continue with your existing code...
            if doi:
                doi = doi.replace("DOI: ", "").strip()  # Strip the "DOI: " prefix
                logger.info(f'DOI scraped by GPT-3: {doi}')
                sanitized_filename = handle_doi(doi)

        # If no DOI is provided or found, or if DOI handling fails
        if sanitized_filename is None:
            file_name = input('Please enter a file name or press Enter to use the original name: ')
            sanitized_filename = sanitize_filename(file_name if file_name else filename)

        txt_file_path = save_text_to_file(text_content, sanitized_filename, output_directory)

        summarize_prompt_input = open_file(r'prompt/doc_summerize_bot_prompt.txt')
        summary_path = summarize(txt_file_path, 
                                 summerize_prompt_input = summarize_prompt_input,
                                 summarize_ratio=float(summarize_ratio))
        
        logger.info(f"Saved summary to {summary_path}")

        move_file(file_path, os.path.join(output_directory, f"{sanitized_filename}.pdf"))
        move_file(txt_file_path, os.path.join(output_directory, f"{sanitized_filename}.txt"))
        
        logger.info(f"Finished loading and processing PDF file from path: {file_path}")
    except Exception as e:
        logger.error(f"Error loading PDF file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Load and process a PDF file.')
    parser.add_argument('file_path', help='The path to the PDF file.')
    parser.add_argument('--output_dir', default='output', help='The directory to save the output files.')
    parser.add_argument('--filename', help='The filename for the output files.')
    parser.add_argument('--ratio', default=0.2, help='The ratio to summarize document tokens')
    args = parser.parse_args()

    try:
        logger.info("Starting PDF file processing")
        load_pdf(args.file_path, args.output_dir, args.filename, args.ratio)
        logger.info("Finished PDF file processing")
    except Exception as e:
        logger.error(f"Error during PDF file processing: {e}")

if __name__ == "__main__":
    main()