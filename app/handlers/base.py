from abc import ABC, abstractmethod


class BaseJobHandler(ABC):
    job_type: str

    @abstractmethod
    def handle(self, payload):
        pass