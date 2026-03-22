from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FlowQueue"
    app_env: str = "development"
    debug: bool = True
    
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_job_events_topic: str = "job-events"

    api_v1_prefix: str = "/api/v1"

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int

    redis_host: str
    redis_port: int
    redis_db: int = 0

    database_url: str
    celery_broker_url: str
    celery_result_backend: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()