import asyncio
import orjson
from utils.logging import logging, log_block_ctx, log_execution_block
from infra.schema import StompFrameModel, InboundMessage, OutboundMessage
from infra.messaging.websocket.session import ws_manager
from services.ingest_service import RagIngestService
from api.deps import _get_ingest_service

logger = logging.getLogger(__name__)


class CommandDispatcher:

    @log_execution_block(title="KafkaConsumerHandler")
    async def dispatch(self, message: dict):
        trace_id = message["key"]
        stomp: StompFrameModel = message["value"]
        # with log_block_ctx(
        #     logger,
        #     f"KafkaConsumerHandler handle key={trace_id}, value={stomp.model_dump()}",
        # ):
        match (stomp.command.lower()):
            case "pipeline-start":
                return await self.pipeline_start(stomp)

            case "query-by-rag":
                return await self.query_by_rag(stomp)

            case _:
                raise ValueError(f"Unknown command received: {message}")

    @log_execution_block(title="pipeline")
    async def pipeline_start(self, stomp: StompFrameModel):
        def __handler(message: dict):
            file_name = message.get("body", "")
            service: RagIngestService = _get_ingest_service()
            return service.ingest_stub(file_name=file_name)

        # ThreadPoolExecutor호출 후, 완료될때까지 대기
        # 에러가 없다면 kafka topic 발행 - topic: pipeline-end
        # 완료 후 websocket broadcast (event loop로 호출)
        result = await asyncio.to_thread(__handler, message=stomp.model_dump())
        if result:
            await ws_manager.broadcast(
                dict(value=dict(answer=f"{stomp.body}: upload completed.")),
                lambda x: True,
            )

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
            logger.info("websocket broadcast completed")
