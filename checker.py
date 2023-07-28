import os
from dotenv import load_dotenv, find_dotenv
from logger import setup_logger

# Load environment variables
load_dotenv(find_dotenv())

# Initialize logger
logger = setup_logger('checker')

def check_openai_connection():
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # TODO: Add your OpenAI connection check here
    # For example, if you're using the openai Python library, you might do something like this:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        openai.Completion.create(engine="text-davinci-002", prompt="test")
    except Exception as e:
        logger.error(f"Failed to connect to OpenAI: {e}")

def check_zotero_connection():
    ZOTERO_API_KEY = os.getenv('ZOTERO_API_KEY')
    ZOTERO_LIBRARY_ID = os.getenv('ZOTERO_LIBRARY_ID')

    # TODO: Add your Zotero connection check here
    # For example, if you're using the pyzotero library, you might do something like this:
    try:
        from pyzotero import zotero
        zot = zotero.Zotero(ZOTERO_LIBRARY_ID, "user", ZOTERO_API_KEY)
        items = zot.top(limit=5)
    except Exception as e:
        logger.error(f"Failed to connect to Zotero: {e}")

def check_directory_access():
    directories = ['ZOTFILE_FOLDER', 'LOG_DIR', 'INPUT_DIR', 'OUTPUT_DIR', 'BACKUP_DIR', 'VECTORS_DIR']
    for directory in directories:
        path = os.getenv(directory)
        if path:
            try:
                # Check read access
                os.listdir(path)
                # Check write access by trying to create a temporary file
                temp_file = os.path.join(path, 'temp_file')
                open(temp_file, 'w').close()
                os.remove(temp_file)
            except Exception as e:
                logger.error(f"Failed to access directory {directory} at {path}: {e}")

def main():
    logger.info("Starting checks...")
    check_openai_connection()
    check_zotero_connection()
    check_directory_access()
    logger.info("Finished checks.")

if __name__ == "__main__":
    main()
