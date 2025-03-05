from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    @abstractmethod
    def process(self, text: str) -> dict:
        """Process the input text and return results"""
        pass
