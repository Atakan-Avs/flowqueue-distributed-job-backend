import time

from app.handlers.base import BaseJobHandler


class ReportJobHandler(BaseJobHandler):
    job_type = "report"

    def handle(self, payload: str) -> str:
        time.sleep(3)

        if "fail" in payload.lower():
            raise ValueError("Simulated report job failure triggered by payload.")

        return f"report generated for payload: {payload}"