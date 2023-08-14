import os
from dotenv import load_dotenv, find_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from file_utils import sanitize_filename, open_file, save_file
# from gpt2brain import llm_core
import openai
from logger import setup_logger
from gpt2brain import OpenAIBrain

# Create a logger for this module
logger = setup_logger(__name__)

# Create a OpenAIBrain instance
brain = OpenAIBrain()

def process_and_summarize_chunks(splits, prompt_input, summarize_ratio = 0.2, attempt_limit = 5):
    note_chunks = []
    try:
        for text_chunk in splits:
            max_tokens = round(len(text_chunk.split()) * summarize_ratio)  # Set max tokens to 20% of input tokens
            
            chunk_input = open_file(r'prompt/summerize_user_prompt.txt').replace('<>', text_chunk)
            
            note_chunk = None
            attempts = 0
            while note_chunk is None and attempts < attempt_limit:  # Retry up to 3 times
                note_chunk = brain.generate_response(prompt_input, chunk_input, max_tokens=max_tokens)
                attempts += 1

            if note_chunk is None:  # Check if the generated response is None
                note_chunk = ""  # If so, replace it with an empty string
                
            note_chunks.append(note_chunk)

        notes = " ".join(note_chunks)
        final_notes_prompt = open_file(r'prompt/final_summerize_bot_prompt.txt')
        max_tokens = round(len(notes.split()))
        
        summary = None
        attempts = 0
        while summary is None and attempts < attempt_limit:
            summary = brain.generate_response(final_notes_prompt, 
                                              notes,
                                              model="gpt-3.5-turbo-16k",
                                              max_tokens=max_tokens)
            attempts += 1
        
        # Similarly, add a check for None here too
        if summary is None:
            summary = ""

        return notes, summary
    except Exception as e:
        logger.error(f"Error during processing and summarizing chunks. Error: {str(e)}")
        raise

def summarize(input_path, summerize_prompt_input, chunk_size = 7000, chunk_overlap = 200, summarize_ratio = 0.2):
    try:
        text = open_file(input_path)
        logger.info(f"Opened input file: {input_path}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = chunk_size,
            chunk_overlap  = chunk_overlap,
            length_function = len,
        )
        
        splits = text_splitter.split_text(text)
        logger.info(f"Split input text into {len(splits)} chunks")
        notes, summary = process_and_summarize_chunks(splits=splits,  prompt_input=summerize_prompt_input, summarize_ratio=summarize_ratio)
        
        # Get 'OUTPUT_DIR' environment variable
        output_dir = os.getenv('OUTPUT_DIR')
        if not output_dir or not os.path.isdir(output_dir):
            logger.error('Output path invalid.')
            return
        
        summary_file_name = f"{os.path.splitext(os.path.basename(input_path))[0]}_summary.md"
        summary_path = os.path.join(output_dir, summary_file_name)
        save_file(summary_path, summary)
        logger.info(f"Saved summary to file: {summary_path}")
        
        return summary_path
    except Exception as e:
        logger.error(f"Error during summarizing. Error: {str(e)}")
        raise