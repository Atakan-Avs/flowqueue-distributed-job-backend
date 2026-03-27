import time

from app.handlers.base import BaseJobHandler


class ScheduledReportJobHandler(BaseJobHandler):
    def handle(self, payload: str) -> str:
        time.sleep(2)

        if "fail" in payload.lower():
            raise ValueError(
                "Simulated scheduled report job failure triggered by payload."
            )

        return f"scheduled report generated for payload: {payload}"