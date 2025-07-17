from llms.llmClientABC import LLMClientABC
from langchain_ollama import ChatOllama

class OllamaClient(LLMClientABC):

    def __init__(self,modelName = "llama3.2"):
        self.modelName = modelName
        self.model = ChatOllama(model=self.modelName)

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content