import asyncio
import orjson
from utils.logging import logging, log_block_ctx, log_execution_block
from infra.schema import StompFrameModel, InboundMessage, OutboundMessage
from infra.messaging.websocket.manager import ws_manager
from services.ingest_service import RagIngestService
from api.deps import get_ingest_service

logger = logging.getLogger(__name__)


class CommandDispatcher:

    @log_execution_block(title="KafkaConsumerHandler")
    async def dispatch(self, message: dict):
        stomp: StompFrameModel = message["value"]
        match (stomp.command.lower()):
            case "pipeline-start":
                return await self.pipeline_start(stomp)

            case "query-by-rag":
                return await self.query_by_rag(stomp)

            case _:
                raise ValueError(f"Unknown command received: {message}")

    @log_execution_block(title="pipeline")
    async def pipeline_start(self, stomp: StompFrameModel):
        async def __handler(message: dict):
            file_name = message.get("body", "")
            service: RagIngestService = get_ingest_service()
            return await service.ingest_stub(file_name=file_name)

        async def _run_and_notify():
            try:
                result = await __handler(stomp.model_dump())
                if result:
                    await ws_manager.broadcast(
                        dict(
                            value=dict(
                                answer=f"{stomp.body}: upload completed.",
                                hits=[],
                            ),
                        ),
                        lambda x: True,
                    )
            except Exception as e:
                logger.error("Error in pipeline_start: %s", exc_info=e)

        # ThreadPoolExecutor호출 후, 완료될때까지 대기
        # 에러가 없다면 kafka topic 발행 - topic: pipeline-end
        # 완료 후 websocket broadcast (event loop로 호출)
        # result = await asyncio.to_thread(__handler, message=stomp.model_dump())

        # 기존 루프와 병렬로 실행 (fire-and-forget + 후처리)
        asyncio.create_task(_run_and_notify())

    @log_execution_block(title="query_by_rag")
    async def query_by_rag(self, stomp: StompFrameModel):

        def _handler(message: dict):
            logger.info("background job: %s", message)
            from api.deps import _rag_query_service as svc

            result = svc.chat(
                query=message["query"],
                filter=message["filter"],
                top_k=message["top_k"],
                llm_model=message["llm"],
                retriever_name=message["retriever"],
            )
            logger.info("LLM answers: %s", result.model_dump())
            return result

        result = await asyncio.to_thread(_handler, message=orjson.loads(stomp.body))
        if result:
            await ws_manager.broadcast(
                dict(value=result.model_dump()),
                lambda x: True,
            )
            logger.info(f"websocket broadcast completed: {result.model_dump()}")
