import os
import requests
import time
from dotenv import load_dotenv, find_dotenv
from pyzotero import zotero

# Import setup_logger from logger.py
from logger import setup_logger

# Initialize the logger
logger = setup_logger('zotero_hook')

# Load Zotero user ID and API key from environment variables
def load_env_vars():
    load_dotenv(find_dotenv())
    zotero_user_id = os.getenv('ZOTERO_LIBRARY_ID')
    zotero_api_key = os.getenv('ZOTERO_API_KEY')
    if not zotero_user_id or not zotero_api_key:
        logger.error('Zotero credentials not found in environment variables')
        raise ValueError('Zotero credentials not found in environment variables')
    return zotero_user_id, zotero_api_key

zotero_user_id, zotero_api_key = load_env_vars()

# Retrieve metadata for a given DOI from the CrossRef API
def fetch_crossref_data(doi):
    crossref_url = f"https://api.crossref.org/works/{doi}"
    crossref_res = requests.get(crossref_url)
    if crossref_res.status_code != 200:
        logger.error(f'Failed to fetch data from CrossRef for DOI: {doi}')
        new_doi = input('Please manually enter a DOI or press Enter to skip: ')
        if new_doi != '':
            return fetch_crossref_data(new_doi)
        else:
            raise ValueError('No valid DOI provided')
    return crossref_res.json()

# Create a Zotero item based on the metadata obtained from CrossRef
def create_item_data(crossref_data):
    zot = zotero.Zotero(zotero_user_id, 'user', zotero_api_key)
    zotero_item = zot.item_template('journalArticle') # Retrieve Zotero template for journal articles

    # Map CrossRef metadata fields to Zotero item fields
    message = crossref_data.get('message', {})
    zotero_item['title'] = message.get('title', [''])[0]
    authors = message.get('author', [])
    zotero_item['creators'] = [{'creatorType': 'author', 'firstName': author.get('given', ''), 'lastName': author.get('family', '')} for author in authors]
    zotero_item['publicationTitle'] = message.get('container-title', [''])[0]
    zotero_item['DOI'] = message.get('DOI', '')
    zotero_item['url'] = message.get('URL', '')
    zotero_item['volume'] = message.get('volume', '')
    zotero_item['issue'] = message.get('issue', '')
    zotero_item['pages'] = message.get('page', '')
    zotero_item['ISSN'] = message.get('ISSN', [''])[0]
    zotero_item['abstractNote'] = message.get('abstract', '')

    # Handle date fields
    published_print = message.get('published-print', message.get('published-online', {}))
    date_parts = published_print.get('date-parts', [['', '', '']])[0]
    zotero_item['date'] = '-'.join([str(part) for part in date_parts if part])

    return zotero_item

# Add the created Zotero item to the Zotero library
def create_zotero_item(zot, item_data):
    created_items = zot.create_items([item_data])
    if not created_items.get('successful'):
        logger.error('Failed to create Zotero item')
        raise ValueError('Failed to create Zotero item')
    return created_items['successful']['0']['key']

# Fetch the newly created Zotero item
def fetch_zotero_item(zot, item_key):
    item = zot.item(item_key)
    if not item:
        logger.error('Failed to fetch Zotero item')
        raise ValueError('Failed to fetch Zotero item')
    return item

# Extract the Better BibTeX citation key from the Zotero item
def extract_citation_key(item):
    extra = item['data'].get('extra', '')
    for line in extra.splitlines():
        if line.startswith("Citation Key: "):
            return line[len("Citation Key: "):]
    logger.error('Failed to extract citation key from Zotero item')
    raise ValueError('Failed to extract citation key from Zotero item')

# Main function to add an item to Zotero by DOI
def add_item_by_doi(doi):
    # Remove any DOI prefixes
    doi = doi.replace('https://doi.org/', '').replace('doi.org/', '')
    
    try:
        # Fetch CrossRef data, create Zotero item data, add item to Zotero
        crossref_data = fetch_crossref_data(doi)
        zot = zotero.Zotero(zotero_user_id, 'user', zotero_api_key)
        item_data = create_item_data(crossref_data)
        item_key = create_zotero_item(zot, item_data)

        # Trigger a Zotero sync
        zot.top(limit=1)

        # Retry loop for fetching Zotero item and extracting citation key
        for _ in range(5):
            zot.top(limit=1)
            time.sleep(10)
            try:
                item = fetch_zotero_item(zot, item_key)
                return extract_citation_key(item)
            except ValueError:
                continue

        logger.error('Failed to extract citation key from Zotero item after multiple attempts')
        raise ValueError('Failed to extract citation key from Zotero item after multiple attempts')
    except Exception as e:
        logger.error(f'Failed to add item to Zotero by DOI. Error: {e}')
        raise e