from __future__ import annotations

import asyncio
import orjson
from typing import Callable
from datetime import datetime
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from utils.logging import logging, log_block_ctx
from schemas.stomp import InboundMessage, OutboundMessage, StompFrameModel
import time

logger = logging.getLogger(__name__)


class KafkaBridge:
    # singleton
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def config(
        self,
        servers: str,
        group: str,
        tin: str,
        tout: str,
        event_loop: asyncio.AbstractEventLoop | None = None,
        consumer_callback: Callable | None = None,
    ):
        self._servers = servers
        self._group = group
        self._tin = tin
        self._tout = tout
        self._event_loop = event_loop
        self._consumer_callback = consumer_callback

        self._producer: AIOKafkaProducer | None = None
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._servers,
            acks="all",
            enable_idempotence=True,
            linger_ms=5,
            key_serializer=lambda key: (
                key.encode("utf-8") if isinstance(key, str) else None
            ),
            value_serializer=lambda x: orjson.dumps(x),
        )
        await self._producer.start()
        # key_deserializer 설정을 별도로 하지 않음. 추가했을때 알수없는 오류가 발생하기도함
        self._consumer = AIOKafkaConsumer(
            self._tout,
            bootstrap_servers=self._servers,
            # group_id=f"{self._group}-{datetime.now().timestamp()}",
            group_id=self._group,
            auto_offset_reset="latest",
            # auto_offset_reset="earliest",
            enable_auto_commit=False,
            auto_commit_interval_ms=1000,
            max_poll_records=10,
            session_timeout_ms=30000,  # broker가 최대한 heartbeat를 대기하는 기간(30초)
            heartbeat_interval_ms=3000,  # consumer가 broker에게 3초마다 신호를 보냄
            max_poll_interval_ms=300000,  # 처리 오래걸릴 때
            value_deserializer=lambda x: orjson.loads(x.decode("utf-8")),
        )
        await self._consumer.start()

        self._task = asyncio.create_task(self._consume_loop())
        self._task.add_done_callback(
            lambda t: logger.error("consumer task ended: %s", t.exception())
        )

        logger.info("KafkaBridge started")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()
        logger.info("KafkaBridge stopped")

    def consumer_callback(self, callback: Callable):
        self._consumer_callback = callback

    def set_event_loop(self, loop: asyncio.AbstractEventLoop | None) -> None:
        self._event_loop = loop

    async def send_message(self, topic: str, **kwargs) -> None:
        assert self._producer is not None
        await self._producer.send_and_wait(topic, **kwargs)

    def send_message_sync(self, topic: str, **kwargs) -> None:
        assert self._producer is not None

        if self._event_loop is None:
            logger.error("event loop is not set")
            return
        asyncio.run_coroutine_threadsafe(
            self._producer.send(topic, **kwargs),
            self._event_loop,
        )

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        logger.info("KafkaBridge _consume_loop start")

        count = 0
        last_commit_time = time.time()
        COMMIT_INTERVAL = 5.0  # 5초마다 commit
        try:
            async for rec in self._consumer:
                if rec.value is None:
                    continue
                """
                consumer value_deserializer에서 orjson설정 처리
                try:
                    value = orjson.loads(rec.value)
                except orjson.JSONDecodeError:
                    value = rec.value              
                """
                with log_block_ctx(
                    logger, f"KafkaBridge received message: {rec.value}"
                ):

                    message_data = {
                        "topic": rec.topic,
                        "partition": rec.partition,
                        "offset": rec.offset,
                        "key": rec.key.decode("utf-8") if rec.key else None,
                        "value": StompFrameModel.model_validate(rec.value),
                        "headers": rec.headers,
                        "timestamp": rec.timestamp,
                        "consumed_at": datetime.now().isoformat(),
                    }

                    if self._consumer_callback:
                        asyncio.create_task(self._consumer_callback(message_data))
                    else:
                        logger.info(
                            "No Callback: KafkaBridge decoded message: %s", message_data
                        )

                # 커밋
                count += 1
                now = time.time()

                # 10개 또는 5초마다 commit
                if count >= 10 or (now - last_commit_time) >= COMMIT_INTERVAL:
                    await self._consumer.commit()
                    logger.info(f"Batch commit: {count} message(s)")
                    count = 0
                    last_commit_time = now

        except asyncio.CancelledError:
            return

        logger.info("KafkaBridge _consume_loop end")


from utils.websocket_utils import hub


async def kafka_to_ws(m: OutboundMessage) -> None:
    body_json = orjson.dumps(m.body).decode("utf-8")
    await hub.broadcast(m.destination, body_json)


# kafkaService = KafkaBridge(
#     servers=settings.kafka_bootstrap_servers,
#     group=settings.kafka_group,
#     tin=settings.kafka_topic,
#     tout=settings.kafka_topic,
# )
