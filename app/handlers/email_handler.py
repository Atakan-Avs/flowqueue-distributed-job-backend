import time

from app.handlers.base import BaseJobHandler


class EmailJobHandler(BaseJobHandler):
    job_type = "email"

    def handle(self, payload: str) -> str:
        time.sleep(2)

        if "fail" in payload.lower():
            raise ValueError("Simulated email job failure triggered by payload.")

        return f"email sent for payload: {payload}"