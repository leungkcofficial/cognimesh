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

def process_and_summarize_chunks(splits, prompt_input, summarize_ratio = 0.2):
    note_chunks = []
    try:
        for text_chunk in splits:
            max_tokens = round(len(text_chunk.split()) * summarize_ratio)  # Set max tokens to 20% of input tokens
            
            chunk_input = open_file(r'prompt/summerize_user_prompt.txt').replace('<>', text_chunk)
            
            note_chunk = brain.generate_response(prompt_input, chunk_input, max_tokens=max_tokens)
            note_chunks.append(note_chunk)

        notes = " ".join(note_chunks)
        final_notes_prompt = open_file(r'prompt/final_summerize_bot_prompt.txt')
        summary = brain.generate_response(final_notes_prompt, 
                                          notes,
                                          model="gpt-3.5-turbo-16k")

        return notes, summary
    except Exception as e:
        logger.error(f"Error during processing and summarizing chunks. Error: {str(e)}")
        raise

def summarize(input_path, summerize_prompt_input, chunk_size = 3000, chunk_overlap = 200, summarize_ratio = 0.2):
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
        
        # Ensure 'output' directory exists
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        summary_file_name = f"{os.path.splitext(os.path.basename(input_path))[0]}_summary.md"
        summary_path = os.path.join(output_dir, summary_file_name)
        save_file(summary_path, summary)
        logger.info(f"Saved summary to file: {summary_path}")
        
        return summary_path
    except Exception as e:
        logger.error(f"Error during summarizing. Error: {str(e)}")
        raise