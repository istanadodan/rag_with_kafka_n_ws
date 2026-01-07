from typing import Any, Protocol
from utils.logging import logging, log_block_ctx
from schemas.stomp import StompFrameModel, InboundMessage, OutboundMessage
from services.kafka.kafka_bridge import KafkaBridge
from core.config import settings
from utils.websocket_utils import ws_manager
import asyncio
import cmn.event_loop as el
from services.ingest_service import RagIngestService
from api.v1.deps import _get_ingest_service
import orjson

logger = logging.getLogger(__name__)


class BaseHandler(Protocol):

    def handle(self, message: dict) -> None: ...


class PipelineHandler(BaseHandler):

    def handle(self, message: dict) -> None:
        from services.ingest_service import RagIngestService
        from api.v1.deps import _get_ingest_service

        service: RagIngestService = _get_ingest_service()
        service.ingest_stub(file_name=message.get("body", ""))


def pipeline_handler(message: dict):

    file_name = message.get("body", "")

    service: RagIngestService = _get_ingest_service()
    return service.ingest_stub(file_name=file_name)


def chat_handler(req: dict):

    #     logger.info("background job: %s", req)
    #     from api.v1.deps import _rag_query_service as svc

    #     result = await svc.chat(query=req["query"], filter=req["filter"], top_k=req["top_k"])
    #     logger.info("background result: %s", result.model_dump_json())

    #     # websocket으로 반환
    #     await ws_manager.broadcast(
    #         dict(value=result.model_dump_json()),
    #         lambda x: True,
    #     )

    logger.info("background job: %s", req)
    from api.v1.deps import _rag_query_service as svc

    result = svc.chat(
        query=req["query"],
        filter=req["filter"],
        top_k=req["top_k"],
        llm_model=req["llm"],
        retriever_name=req["retriever"],
    )
    logger.info("background result: %s", result.model_dump())
    return result


async def kafka_consumer_handler(message: dict) -> None:

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
                with log_block_ctx(logger, f"pipeline: {message}"):
                    # ThreadPoolExecutor호출 후, 완료될때까지 대기
                    result = await asyncio.to_thread(
                        pipeline_handler, message=stomp.model_dump()
                    )
                    # 에러가 없다면 kafka topic 발행 - topic: pipeline-end
                    # 완료 후 websocket broadcast (event loop로 호출)
                    if result:
                        await ws_manager.broadcast(
                            dict(value=dict(answer=f"{stomp.body}: upload completed.")),
                            lambda x: True,
                        )

                        # kafka_service = KafkaBridge()
                        # topic = settings.kafka_topic
                        # with log_block_ctx(logger, f"send kafka topic({topic})"):
                        #     kafka_service.send_message_sync(
                        #         topic=topic,
                        #         key=trace_id,
                        #         value=StompFrameModel(
                        #             command="pipeline-end",
                        #             headers={},
                        #             body=stomp.body,
                        #         ).model_dump(),
                        #     )

            # case "pipeline-end":
            #     with log_block_ctx(logger, f"pipeline-end ws send: {message}"):
            #         await ws_manager.broadcast(
            #             dict(value=dict(answer=f"{stomp.body}: upload completed.")),
            #             lambda x: True,
            #         )

            case "query-by-rag":
                with log_block_ctx(logger, f"query-by-rag ws send: {message}"):
                    result = await asyncio.to_thread(
                        chat_handler, req=orjson.loads(stomp.body)
                    )
                    if result:
                        await ws_manager.broadcast(
                            dict(value=result.model_dump()),
                            lambda x: True,
                        )
                        logger.info("websocket broadcast completed")

            case _:
                raise ValueError(f"Unknown command received: {message}")
