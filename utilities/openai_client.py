import os
import re
import logging
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.tools import BaseTool, FunctionTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenAiClient:
    def __init__(self):
        self.model = "gpt-4o"
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("No OpenAI API key found. Please set the OPENAI_KEY environment variable.")
        self.llm = OpenAI(model=self.model, api_key=self.api_key, max_tokens=6122)
        self.agent = ReActAgent.from_tools(llm=self.llm, max_iterations=10)

    def chat(self, prompt):
        logger.info("Sending prompt to OpenAI: %s", prompt)
        response = self.llm.complete(prompt).text
        return response