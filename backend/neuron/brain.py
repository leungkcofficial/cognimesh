import openai
from ..settings.settings import Setting
from logger import setup_logger
import asyncio
from ..axon.file_utils import sanitize_filename, open_file, save_file, move_file, delete_file, copy_file, rename_file

logger = setup_logger(__name__)

class Brain:
    def __init__(self):
        settings = Setting()
        self.api_key = settings.openai_api_key
        openai.api_key = self.api_key
        logger.info("Brain initialized with OpenAI API key.")

    async def _query_api(self, model, prompt, is_chat_model=False, **kwargs):
        """Internal method to perform the actual query to the OpenAI API."""
        try:
            if is_chat_model:
                return openai.ChatCompletion.create(
                    model=model, messages=[{"role": "user", "content": prompt}], **kwargs
                )
            else:
                return openai.Completion.create(
                    model=model, prompt=prompt, **kwargs
                )
        except Exception as e:
            logger.error(f"Error querying the LLM: {e}")
            return None

    async def query_async(self, model, prompt, is_chat_model=False, **kwargs):
        # Asynchronous querying logic...
        return await self._query_api(model, prompt, is_chat_model, **kwargs)
    
    def query(self, model, prompt, is_chat_model=False, **kwargs):
        # Synchronous querying logic...
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._query_api(model, prompt, is_chat_model, **kwargs))