from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "rag-api"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    qdrant_url: str = os.getenv("QDRANT_URL", "qdrant")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "it_tech_db")

    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "768"))
    pdf_dir: str = os.getenv("PDF_DIR", "/mnt")

    kafka_enabled: bool = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
    kafka_bootstrap_servers: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "kafka-0.kafka-headless.rag.svc.cluster.local:9092,kafka-1.kafka-headless.rag.svc.cluster.local:9092",
    )
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "rag_ingestion_start")
    kafka_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "group-01")


settings = Settings()
