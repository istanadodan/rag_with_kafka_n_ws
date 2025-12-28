from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    app_name: str = "rag-api"
    log_level: str = "INFO"

    qdrant_url: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection: str = "it_tech_db"

    embedding_dim: int = 768
    pdf_dir: str = "/mnt"
    chunk_size: int = 500
    chunk_overlap: int = 50

    kafka_enabled: bool = True
    kafka_bootstrap_servers: str = (
        "kafka-0.kafka-headless.rag.svc.cluster.local:9092,kafka-1.kafka-headless.rag.svc.cluster.local:9092"
    )
    kafka_topic: str = "rag_ingestion_start"
    kafka_group: str = "group-01"

    openai_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
