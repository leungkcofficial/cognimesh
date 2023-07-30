import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
from logger import setup_logger
from file_utils import sanitize_filename, open_file, save_file
from summarizer import summarize
import argparse

import requests
from bs4 import BeautifulSoup

# Create a logger for this module
logger = setup_logger(__name__)

def scrape_webpage(url):
    """
    Scrapes the webpage at the given URL and returns the page title and text content.

    Parameters:
    url (str): URL of the webpage to scrape.

    Returns:
    tuple: page title (str), page text content (str)
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.title.string
    text_content = ' '.join([p.get_text() for p in soup.find_all('p')])

    return title, text_content

def load_html(url, filename=None, ratio=0.2):
    """
    Loads a webpage, scrapes the text, and saves the text to a new file.

    Parameters:
    url (str): URL of the webpage to load.
    filename (str): Name of the output text file (optional).
    ratio (float): The ratio to summarize document tokens (optional).

    Returns:
    None
    """
    try:
        logger.info(f"Loading webpage from URL: {url}")

        title, text_content = scrape_webpage(url)

        filename = filename if filename else title
        sanitized_filename = sanitize_filename(filename)

        # Retrieve the output directory from environment variable
        output_directory = os.getenv('OUTPUT_DIR')
        if not output_directory:
            raise Exception("Output path environment variable not set")

        # # Prepare the output directory
        # os.makedirs(output_directory, exist_ok=True)

        # Prepare the output file path
        txt_file_path = os.path.join(output_directory, f"{sanitized_filename}.txt")

        # Save the text content to the output file
        with open(txt_file_path, "w") as text_file:
            text_file.write(text_content)

        logger.info(f"Saved webpage content to file: {txt_file_path}")

        # Summarize the document
        summarize_prompt_input = open_file(r'prompt/html_bot_prompt.txt')
        summary_path = summarize(txt_file_path, summarize_prompt_input, summarize_ratio=ratio)

        logger.info(f"Saved summary to file: {summary_path}")
    except Exception as e:
        logger.error(f"Error loading webpage: {e}")

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description='Load a webpage, scrape the text, and save the text to a new file.')
    parser.add_argument('--url', help='URL of the webpage to load')
    parser.add_argument('--filename', default=None, help='Name of the output text file')
    parser.add_argument('--ratio', default=0.2, type=float, help='The ratio to summarize document tokens')

    args = parser.parse_args()

    # Call the function with arguments
    load_html(args.url, args.filename, args.ratio)

if __name__ == "__main__":
    main()
