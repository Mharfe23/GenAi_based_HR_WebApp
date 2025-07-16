from abc import ABC, abstractmethod

class LLMClientABC(ABC):
    @abstractmethod
    def generate(self,prompt: str) -> str:
        pass