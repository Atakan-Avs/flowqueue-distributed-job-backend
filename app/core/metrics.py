from prometheus_client import Counter

jobs_created_total = Counter(
    "flowqueue_jobs_created_total",
    "Total number of jobs created",
)

jobs_completed_total = Counter(
    "flowqueue_jobs_completed_total",
    "Total number of jobs completed successfully",
)

jobs_failed_total = Counter(
    "flowqueue_jobs_failed_total",
    "Total number of failed job executions",
)

jobs_dead_letter_total = Counter(
    "flowqueue_jobs_dead_letter_total",
    "Total number of jobs moved to dead letter queue",
)

job_retries_total = Counter(
    "flowqueue_job_retries_total",
    "Total number of job retries",
)