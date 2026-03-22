from abc import ABC, abstractmethod


class BaseJobHandler(ABC):
    @abstractmethod
    def handle(self, payload: str) -> str:
        pass