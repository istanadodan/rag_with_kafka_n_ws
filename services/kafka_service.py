import asyncio
import json
from kafka import KafkaConsumer, KafkaProducer
from core.config import settings
from typing import Generator
from dataclasses import dataclass
from datetime import datetime
from utils.logging import logging, log_block_ctx
from services.kafka_handlers import BaseHandler
from utils.thread_utils import ThreadExecutor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka 연결 설정을 담당하는 불변 객체"""

    # topic: str
    bootstrap_servers: str
    group_id: str
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    consumer_timeout_ms: int = 30000  # polling 타임아웃
    max_poll_records: int = 500  # 한 번에 가져올 최대 레코드 수
    reconnect_backoff_ms: int = 50  # 재연결 대기 시간

    @classmethod
    def from_settings(cls, servers: str, group_id: str = "group-01") -> "KafkaConfig":
        """설정으로부터 KafkaConfig 생성"""
        return cls(
            bootstrap_servers=servers,
            group_id=group_id,
        )


class KafkaConsumerService:
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        # 토픽 추출
        self.consumer = KafkaConsumer(
            topic,
            value_deserializer=lambda x: x.decode("utf-8"),
            **KafkaConfig.from_settings(bootstrap_servers, group_id).__dict__,
        )

    def consume(self) -> Generator:
        for message in self.consumer:
            yield message

    def close(self):
        self.consumer.close()


class KafkaConsumerBackgroundService(BaseHandler):
    """
    요구사항: '수신만 고려' + FastAPI 내부 백그라운드 태스크.
    현재는 연결/구독은 스텁으로 두고, 향후 aiokafka 등으로 교체.
    """

    def __init__(self, message_handler: BaseHandler, **kwargs):
        # self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._msg_handler = message_handler
        self.kwargs = kwargs or {}
        self._consumer: KafkaConsumerService | None = None
        self._thread: ThreadExecutor | None = None

    def create_consumer(self, **kwargs) -> None:
        self.kwargs.update(kwargs or {})
        self._consumer = KafkaConsumerService(**self.kwargs)

    def start(self) -> None:
        if not settings.kafka_enabled:
            logger.info("Kafka consumer disabled (KAFKA_ENABLED=false).")
            return
        if self._consumer is None:
            self.create_consumer()
        if self._thread is None:
            self._thread = ThreadExecutor(task=self)
        self._thread.submit()
        logger.info("Kafka consumer starting (stub). topic=%s", settings.kafka_topic)

    def stop(self) -> None:
        # self._stop.set()
        if self._consumer:
            logger.info("Kafka consumer terminated")
            self._consumer.close()

        if self._thread:
            logger.info("Kafka consumer thread terminated")
            self._thread.shutdown()

    def handle(self, message) -> None:
        # 스텁: 실제로는 topic 수신 후 pdf_dir에 떨어진 파일 ingest 트리거 등으로 확장
        if self._consumer is None:
            logger.error("Kafka consumer not initialized.")
            return

        logger.info("Kafka consumer heartbeat (stub) starts")
        while True:

            msg = next(self._consumer.consume(), None)

            if msg is not None:
                try:
                    value = json.loads(msg.value)
                except json.JSONDecodeError:
                    value = msg.value

                message_data = {
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "key": msg.key.decode("utf-8") if msg.key else None,
                    "value": value,
                    "headers": msg.headers,
                    "timestamp": msg.timestamp,
                    "consumed_at": datetime.now().isoformat(),
                }

                logger.info("Kafka consumer received message: %s", message_data)
                if self._msg_handler:
                    self._msg_handler.handle(message_data)


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda key: (
                key.encode("utf-8") if isinstance(key, str) else key
            ),
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

    def send_message(self, topic: str, **kwargs) -> None:
        logger.info("Kafka producer sending message: %s", kwargs)
        try:
            # topic, value=None, key=None, headers=None, partition=None, timestamp_ms=None
            self._producer.send(topic, **kwargs)
            self._producer.flush()
        except Exception as e:
            logger.error("Kafka producer error: %s", str(e))

    def close(self):
        self._producer.close()
