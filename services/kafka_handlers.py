from typing import Any, Protocol
from utils.logging import logging, log_block_ctx
from schemas.stomp import StompFrameModel, InboundMessage, OutboundMessage
from services.kafka_bridge import KafkaBridge
from core.config import settings

import asyncio

logger = logging.getLogger(__name__)


class BaseHandler(Protocol):

    def handle(self, message: dict) -> None: ...


class PipelineHandler(BaseHandler):

    def handle(self, message: dict) -> None:
        from services.ingest_service import RagIngestService
        from api.v1.deps import _get_ingest_service

        service: RagIngestService = _get_ingest_service()
        service.ingest_stub(file_name=message.get("body", ""))


async def pipeline_handler(message: dict):

    def _background_job(file_name: str):
        from services.ingest_service import RagIngestService
        from api.v1.deps import _get_ingest_service

        service: RagIngestService = _get_ingest_service()
        return service.ingest_stub(file_name=file_name)

    return await asyncio.to_thread(_background_job, file_name=message.get("body", ""))


async def kafka_consumer_handler(message: dict) -> None:
    from utils.thread_utils import ThreadExecutor, Future
    import asyncio

    with log_block_ctx(logger, "Kafka Consumer - Handler"):
        trace_id = message["key"]
        stomp: StompFrameModel = message["value"]
        logger.info(
            "KafkaConsumerHandler handle key=%s, value=%s",
            trace_id,
            stomp.model_dump(),
        )
        match (stomp.command.lower()):
            case "pipeline-start":
                # thread_runner = ThreadExecutor(task=PipelineHandler())
                # def _notify_outbound(future: Future):
                #     try:
                #         # callback에서 에러발생여부 체크
                #         logger.info(f"fucture result: {future.result()}")
                #     except Exception as e:
                #         return

                #     kafka_service = KafkaBridge()
                #     # 완료 후 websocket broadcast (event loop로 호출)
                #     # kafka topic 발행 - topic: pipeline-end
                #     topic = settings.kafka_topic
                #     with log_block_ctx(logger, f"send kafka topic({topic})"):
                #         kafka_service.send_message_sync(
                #             topic=topic,
                #             key=trace_id,
                #             value=StompFrameModel(
                #                 command="pipeline-end",
                #                 headers={},
                #                 body=stomp.body,
                #             ).model_dump(),
                #         )

                # thread에서 호출
                # future = thread_runner.submit(message=stomp.model_dump())
                # future.add_done_callback(_notify_outbound)

                def _notify_outbound2(task: asyncio.Task):
                    logger.info(f"_notify_outbound2 task: {task}")
                    if not task.result():
                        logger.info(f"UI notify, cancelled due to an error!")
                        return

                    kafka_service = KafkaBridge()
                    # 완료 후 websocket broadcast (event loop로 호출)
                    # kafka topic 발행 - topic: pipeline-end
                    topic = settings.kafka_topic
                    with log_block_ctx(logger, f"send kafka topic({topic})"):
                        kafka_service.send_message_sync(
                            topic=topic,
                            key=trace_id,
                            value=StompFrameModel(
                                command="pipeline-end",
                                headers={},
                                body=stomp.body,
                            ).model_dump(),
                        )

                task = asyncio.create_task(pipeline_handler(message=stomp.model_dump()))
                task.add_done_callback(_notify_outbound2)

            case "pipeline-end":
                logger.info("websocket broadcast: %s", message)
                import asyncio
                from utils.websocket_utils import ws_manager
                import cmn.event_loop as el

                if el.MAIN_LOOP is None:
                    logger.error("event loop is not running")
                    return
                asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast(
                        dict(value=f"{stomp.body}: upload completed."),
                        lambda x: True,
                    ),
                    el.MAIN_LOOP,
                )
                return
            case _:
                raise ValueError(f"Unknown command received: {message}")
