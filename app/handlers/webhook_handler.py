import time

from app.handlers.base import BaseJobHandler


class WebhookJobHandler(BaseJobHandler):
    def handle(self, payload: str) -> str:
        time.sleep(1)

        if "fail" in payload.lower():
            raise ValueError("Simulated webhook job failure triggered by payload.")

        return f"webhook delivered for payload: {payload}"