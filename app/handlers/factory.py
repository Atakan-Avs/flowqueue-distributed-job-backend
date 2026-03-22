from app.handlers.email_handler import EmailJobHandler
from app.handlers.report_handler import ReportJobHandler
from app.handlers.webhook_handler import WebhookJobHandler


class JobHandlerFactory:
    @staticmethod
    def get_handler(job_type: str):
        normalized_job_type = job_type.strip().lower()

        if normalized_job_type == "email":
            return EmailJobHandler()

        if normalized_job_type == "report":
            return ReportJobHandler()

        if normalized_job_type == "webhook":
            return WebhookJobHandler()

        raise ValueError(f"Unsupported job type: {job_type}")