#Imports
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .prompts import SYSTEM_PROMPT
import os

#load the env variable
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise Exception("API key is not set in env set GEMINI_API_KEY ")

model = os.getenv("MODEL")
if not model:
    raise Exception("Model key is not set in env set MODEL ")

client = genai.Client(api_key = api_key)
#custom wrapper
class Chat():
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def response(self, question: str):  
        grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

        config = types.GenerateContentConfig(
                tools=[grounding_tool],
                system_instruction=SYSTEM_PROMPT
            )
        response = self.client.models.generate_content(model = self.model, contents = question, config = config)

        output = response.text
        return output


