import os, whisper
from yt_dlp import YoutubeDL
import argparse

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

from file_utils import sanitize_filename, open_file, save_file, move_file, delete_file
from summarizer import summarize
# Import setup_logger from logger.py
from logger import setup_logger

# Initialize the logger
logger = setup_logger('yt_loader')

# Retrieve paths from environment variables
INPUT_PATH = os.getenv('INPUT_PATH')
OUTPUT_PATH = os.getenv('OUTPUT_PATH')
LOG_PATH = os.getenv('LOG_PATH')

def download_audio_from_youtube(url):
    try:
        logger.info(f"Downloading audio from YouTube URL: {url}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': '/usr/bin/ffmpeg',  # Replace with your ffmpeg path
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', None)
            video_title = sanitize_filename(video_title)
        
        input_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input')
        os.makedirs(input_directory, exist_ok=True)
        path_template = os.path.join(input_directory, f'{video_title}.%(ext)s')
        
        ydl_opts.update({'outtmpl': path_template})

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        output_path = path_template % {'ext': 'mp3'}
        
        return output_path

    except Exception as e:
        logger.error(f"Error downloading audio from YouTube: {e}")

def transcribe_audio_file(output_path):
    try:
        logger.info(f"Transcribing audio file: {output_path}")
        
        # Get base name of the original audio file
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        transcript_path = os.path.join(os.path.dirname(output_path), f"{base_name}.md")

        model = whisper.load_model('base')
        transcript = model.transcribe(output_path, fp16=False)
        
        save_file(transcript_path, content=transcript["text"])

        return transcript_path  # Return the path to the transcript text file
    
    except Exception as e:
        logger.error(f"Error transcribing audio file: {e}")

def load_yt(url):
    try:
        logger.info(f"Loading YouTube video from URL: {url}")
        
        output_path = download_audio_from_youtube(url)
        transcript_path = transcribe_audio_file(output_path)
        summerize_prompt_input = open_file(r'prompt/yt_summerize_bot_prompt.txt')
        summary_path = summarize(transcript_path, 
                                 summerize_prompt_input = summerize_prompt_input)
        # get directory of summary file
        summary_dir = os.path.dirname(summary_path)

        # create new paths in summary directory
        new_output_path = os.path.join(summary_dir, os.path.basename(output_path))
        new_transcript_path = os.path.join(summary_dir, os.path.basename(transcript_path))

        # move files to summary directory
        move_file(output_path, new_output_path)
        move_file(transcript_path, new_transcript_path)
        
        return summary_path
    
    except Exception as e:
        logger.error(f"Error loading YouTube video: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download, transcribe, and summarize a YouTube video.")
    parser.add_argument("url", help="The URL of the YouTube video to process.")
    args = parser.parse_args()
    
    try:
        logger.info("Starting YouTube video processing")
        load_yt(args.url)
        logger.info("Finished YouTube video processing")
    except Exception as e:
        logger.error(f"Error during YouTube video processing: {e}")