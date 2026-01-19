from pydantic_settings import BaseSettings
import asyncio

MAIN_LOOP: asyncio.AbstractEventLoop | None = None


class Settings(BaseSettings):
    app_name: str = "rag-api"
    log_level: str = "INFO"

    # DB
    db_url: str = "postgresql+asyncpg://postgres:postgres@postgre:5432/postgres"
    db_echo: bool = False
    db_pool_size: int = 10

    # VDB
    qdrant_url: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection: str = "it_tech_db"

    # PIPELINE
    embedding_model_name: str = "sentence-transformers/all-minilm-l6-v2"
    embedding_dim: int = 768
    pdf_dir: str = "/mnt"
    chunk_size: int = 100
    chunk_overlap: int = 0

    # Messaging
    kafka_enabled: bool = True
    kafka_bootstrap_servers: str = (
        "kafka-0.kafka-headless.rag.svc.cluster.local:9092,kafka-1.kafka-headless.rag.svc.cluster.local:9092"
    )
    kafka_topic: str = "rag_ingestion_start"
    kafka_group: str = "group-01"

    # LLM
    openai_api_key: str = ""
    llm_model_name: str = "studio"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
