import os
from dotenv import load_dotenv, find_dotenv
import openai

# Read local .env file
load_dotenv(find_dotenv())

class OpenAIBrain:
    def __init__(self):
        # Set OpenAI API Key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Please set the OpenAI API key in the environment variables.")
        openai.api_key = api_key

    def generate_response(self, prompt_input, user_input, model="gpt-3.5-turbo-16k", temperature=0.7, 
                          max_tokens=2000, frequency_penalty=0, presence_penalty=0):
        if not prompt_input or not user_input:
            raise ValueError("Prompt input and user input should not be empty.")
        
        messagein = [
            {"role": "system", "content": prompt_input},
            {"role": "user", "content": user_input}
        ]

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messagein,
                temperature=temperature,
                max_tokens=max_tokens,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )
            text = response['choices'][0]['message']['content']
            return text
        except Exception as e:
            print(f"An error occurred while generating text: {e}")
            return None

