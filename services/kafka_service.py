import json, orjson
from kafka import KafkaConsumer, KafkaProducer
from typing import Callable, Union
from dataclasses import dataclass
from datetime import datetime
from threading import Event
from utils.logging import logging, log_block_ctx
from core.config import settings
from services.kafka_handlers import BaseHandler
from utils.thread_utils import ThreadExecutor, Future
from schemas.stomp import StompFrameModel

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka 연결 설정을 담당하는 불변 객체"""

    # topic: str
    bootstrap_servers: str
    group_id: str
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    consumer_timeout_ms: int = 10000  # polling 타임아웃
    max_poll_records: int = 100  # 한 번에 가져올 최대 레코드 수
    reconnect_backoff_ms: int = 50  # 재연결 대기 시간

    @classmethod
    def from_settings(cls, servers: str, group_id: str = "group-01") -> "KafkaConfig":
        """설정으로부터 KafkaConfig 생성"""
        return cls(
            bootstrap_servers=servers,
            group_id=group_id,
        )


class KafkaService:

    def __init__(self, topic: str, group_id: str, bootstrap_servers: str):
        # 토픽 추출
        self._stop_event = Event()
        self.consumer = KafkaConsumer(
            topic,
            value_deserializer=lambda x: orjson.loads(x.decode("utf-8")),
            **KafkaConfig.from_settings(bootstrap_servers, group_id).__dict__,
        )

        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda key: (
                key.encode("utf-8") if isinstance(key, str) else key
            ),
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

    def consumer_callback(self, callback: Union[BaseHandler, Callable]):
        self.callback = callback if isinstance(callback, Callable) else callback.handle

    def send_message(self, topic: str, **kwargs) -> None:
        logger.info("Kafka producer sending message: %s", kwargs)
        try:
            # topic, value=None, key=None, headers=None, partition=None, timestamp_ms=None
            self.producer.send(topic, **kwargs)
            self.producer.flush()
        except Exception as e:
            logger.error("Kafka producer error: %s", str(e))

    def run_thread(self) -> bool:
        self._thread = ThreadExecutor(task=self._poll)
        try:
            _r = self._thread.submit()
            return True
        except Exception:
            logger.error("Kafka consumer thread start failed")
            return False

    def stop(self):
        self._stop_event.set()

    def _close(self):
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer terminated")

        if self._thread:
            self._thread.shutdown()

    def _poll(self, message=None) -> None:
        logger.info("Kafka consumer heartbeat (stub) starts")
        while not self._stop_event.is_set():
            # queue에서 다음 메시지를 가져온다
            for msg in self.consumer:
                if msg is None:
                    continue

                try:
                    try:
                        value = orjson.loads(msg.value)
                    except orjson.JSONDecodeError:
                        value = msg.value

                    message_data = {
                        "topic": msg.topic,
                        "partition": msg.partition,
                        "offset": msg.offset,
                        "key": msg.key.decode("utf-8") if msg.key else None,
                        "value": StompFrameModel.model_validate(value),
                        "headers": msg.headers,
                        "timestamp": msg.timestamp,
                        "consumed_at": datetime.now().isoformat(),
                    }

                    logger.info("Kafka consumer received message: %s", message_data)
                    if self.callback:
                        self.callback(message_data)

                except Exception as e:
                    logger.error("Kafka consumer error: %s", str(e))
                    continue

        self._close()


kafkaService = KafkaService(
    topic=settings.kafka_topic,
    group_id=settings.kafka_group,
    bootstrap_servers=settings.kafka_bootstrap_servers,
)
