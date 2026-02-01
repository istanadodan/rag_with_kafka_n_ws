from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import core.config as config
from core.config import settings
from core.logging import setup_logging
from utils.logging import get_logger

# logging setup
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from infra.messaging.kafka.consumer_handler import kafka_consumer_handler
    from infra.messaging.kafka.aio_kafka import KafkaBridge
    from core.db.rdb import create_tables
    from models.parent_documents import ParentDocument

    # table 생성
    await create_tables()

    # main event loop 저장
    config.MAIN_LOOP = asyncio.get_running_loop()

    """
    동기처리 kafka 사용 시,
    from services.kafka_service import kafkaService

    kafkaService.consumer_callback(KafkaConsumerHandler())
    kafkaService.run_thread()
    """
    kafka_service = KafkaBridge()
    kafka_service.config(
        servers=config.settings.kafka_bootstrap_servers,
        group=config.settings.kafka_group,
        tin=settings.kafka_topic,
        tout=settings.kafka_topic,
        consumer_callback=kafka_consumer_handler,
        event_loop=config.MAIN_LOOP,
    )
    # kafka_service.set_event_loop(el.MAIN_LOOP)
    await kafka_service.start()
    logger.info(
        "App started. collection=%s dim=%d",
        settings.qdrant_collection,
        settings.embedding_dim,
    )
    yield

    # Shutdown
    # kafkaService.stop()
    await kafka_service.stop()
    logger.info("App shutdown completed")


def create_app() -> FastAPI:
    from starlette.middleware.cors import CORSMiddleware
    from core.middleware.trace_id import trace_id_middleware
    from core.middleware.access_log import access_logging_middleware
    from core.exception.handlers import get_exception_handlers
    from api.v1.api_route import router as api_router

    app = FastAPI(title=settings.app_name, lifespan=lifespan, root_path="/rag-api")
    # --- middlewares ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    @app.middleware("http")
    async def _access_logging_middleware(request, call_next):
        return await access_logging_middleware(request, call_next)

    @app.middleware("http")
    async def _trace_id_middleware(request, call_next):
        return await trace_id_middleware(request, call_next)

    # ---- exceptions ---
    app.exception_handlers = get_exception_handlers()
    # ---- Routers ----
    app.include_router(api_router)

    # (선택) operationId 안정화
    # 라우터별 prefix 추가
    # for route in app.routes:
    #     if isinstance(route, APIRoute) and route.operation_id is None:
    #         # 태그 기반으로 안정적인 operationId 생성
    #         tag = route.tags[0] if route.tags else "default"
    #         route.operation_id = f"{tag}_{route.name}"

    return app


app = create_app()
