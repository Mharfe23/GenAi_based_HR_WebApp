from llms.llmClientABC import LLMClientABC
from clients.groq_client import text_to_mongo_query, resume_to_json_with_groq
from groq import Groq
import os
import dotenv

class GroqClient(LLMClientABC):


    def __init__(self, modelName="llama-3.3-70b-versatile"):
        dotenv.load_dotenv()
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.modelName = modelName

    def generate(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
        model=self.modelName,
        messages=[
            {"role": "user", "content": prompt}
        ]
        )
        return completion.choices[0].message.content