from typing import Any, Protocol
from core.config import settings
import logging
import core.event_loop as el

logger = logging.getLogger(__name__)


class BaseHandler(Protocol):
    def handle(self, message: Any) -> None: ...


class PipelineHandler(BaseHandler):

    def handle(self, message: Any) -> None:
        from services.ingest_service import RagIngestService
        from api.v1.deps import _get_ingest_service

        service: RagIngestService = _get_ingest_service()
        service.ingest_stub(file_name=str(message))


class KafkaConsumerHandler(BaseHandler):

    def handle(self, message: Any) -> None:
        from utils.thread_utils import ThreadExecutor
        from services.kafka_handlers import PipelineHandler

        _command = message.get("key", "")
        _message = message.get("value", "")
        handler = {"PDF": PipelineHandler}.get(_command, PipelineHandler)

        if message.get("key") != "pdf":
            thread_runner = ThreadExecutor(task=handler())

            # thread에서 호출
            thread_runner.submit(message=_message)

        # rag pipeline 호출
        # logger.info("Received message: %s and call service", message)
        # loop.run_in_executor(executor, service.ingest_stub, message.get("value", None))
        # service.ingest_stub(file_name=message.get("value", "test"))

        # loop.run_until_complete(
        #     ws_manager.broadcast(
        #         dict(value=f"{message.get("value")}: upload complete"), lambda x: True
        #     )
        # )

        # kafka_producer = KafkaProducerService(
        #     bootstrap_servers=settings.kafka_bootstrap_servers
        # )
        # if message.get("value") == "test":
        #     kafka_producer.send_message(
        #         topic=settings.kafka_topic, message={"value": "test_doc"}
        #     )
        #     logger.info("Send message complete")
