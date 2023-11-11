import openai
from ..settings.settings import Setting
from logger import setup_logger

logger = setup_logger(__name__)

class Brain:
    def __init__(self):
        settings = Setting()
        self.api_key = settings.openai_api_key
        openai.api_key = self.api_key
        logger.info("Brain initialized with OpenAI API key.")

    def query(self, model, prompt, is_chat_model=False, **kwargs):
        """
        Sends a query to the specified LLM using OpenAI's API.

        Args:
            model (str): The model to use for the query.
            prompt (str): The prompt to send to the model.
            is_chat_model (bool): True if the model is a chat model, False otherwise.
            **kwargs: Additional arguments to pass to the OpenAI API.

        Returns:
            The response from the LLM.
        """
        try:
            if is_chat_model:
                logger.info(f"Sending chat query to OpenAI model {model}.")
                response = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": prompt}], **kwargs)
            else:
                logger.info(f"Sending query to OpenAI model {model}.")
                response = openai.Completion.create(model=model, prompt=prompt, **kwargs)
            logger.info("Query successful.")
            return response
        except Exception as e:
            logger.error(f"Error querying the LLM: {e}")
            return None
