import time

from app.handlers.base import BaseJobHandler


class WebhookJobHandler(BaseJobHandler):
    job_type = "webhook"

    def handle(self, payload: str) -> str:
        time.sleep(1)

        if "fail" in payload.lower():
            raise ValueError("Simulated webhook job failure triggered by payload.")

        return f"webhook processed for payload: {payload}"