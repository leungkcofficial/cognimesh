import os
import re
import shutil
import hashlib
import uuid
from logger import setup_logger

# Create a logger for this module
logger = setup_logger(__name__)

def open_file(filepath: str) -> str:
    if not os.path.isfile(filepath):
        raise ValueError(f"{filepath} is not a valid file.")
    try:
        with open(filepath, 'r', encoding='utf-8') as infile:
            content = infile.read()
        logger.info(f"Opened file: {filepath}")
        return content
    except Exception as e:
        logger.error(f"Failed to open file: {filepath}. Error: {str(e)}")
        raise

def save_file(filepath: str, content: str) -> None:
    try:
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(content)
        logger.info(f"Saved file: {filepath}")
    except Exception as e:
        logger.error(f"Failed to save file: {filepath}. Error: {str(e)}")
        raise
        
def sanitize_filename(filename: str) -> str:
    logger.info(f"Sanitizing filename: {filename}")
    sanitized = re.sub(r'\W+', '_', filename).strip('_')
    logger.info(f"Sanitized filename: {sanitized}")
    return sanitized

def delete_file(filepath: str) -> None:
    if not os.path.isfile(filepath):
        raise ValueError(f"{filepath} is not a valid file.")
    os.remove(filepath)
    logger.info(f"Deleted file: {filepath}")

def move_file(source_filepath: str, destination_filepath: str) -> None:
    if not os.path.isfile(source_filepath):
        raise ValueError(f"{source_filepath} is not a valid file.")
    try:
        shutil.move(source_filepath, destination_filepath)
        logger.info(f"Moved file from {source_filepath} to {destination_filepath}")
    except Exception as e:
        logger.error(f"Failed to move file from {source_filepath} to {destination_filepath}. Error: {str(e)}")
        raise

def copy_file(source_filepath: str, destination_filepath: str) -> None:
    if not os.path.isfile(source_filepath):
        raise ValueError(f"{source_filepath} is not a valid file.")
    try:
        shutil.copy(source_filepath, destination_filepath)
        logger.info(f"Copied file from {source_filepath} to {destination_filepath}")
    except Exception as e:
        logger.error(f"Failed to copy file from {source_filepath} to {destination_filepath}. Error: {str(e)}")
        raise

def rename_file(old_path: str, new_path: str) -> None:
    if not os.path.isfile(old_path):
        raise ValueError(f"{old_path} is not a valid file.")
    try:
        os.rename(old_path, new_path)
        logger.info(f"Renamed file {old_path} to {new_path}")
    except Exception as e:
        logger.error(f"Error renaming file from {old_path} to {new_path}. Error: {str(e)}")
        raise

def get_file_size(source_filepath: str) -> int:
    """Get the size of the file in bytes."""
    if not os.path.isfile(source_filepath):
        raise ValueError(f"{source_filepath} is not a valid file.")
    return os.path.getsize(source_filepath)

def compute_sha1_from_file(source_filepath: str):
    with open(source_filepath, "rb") as file:
        bytes = file.read()
        readable_hash = compute_sha1_from_content(bytes)
    return readable_hash

def compute_sha1_from_content(content):
    return hashlib.sha1(content).hexdigest()

def vector_id_from_sha1(sha1: str) -> uuid.UUID:
    return uuid.UUID(sha1[:32])