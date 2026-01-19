from services.dispatchers.command_dispatcher import CommandDispatcher
from utils.logging import log_execution_block
from infra.messaging.websocket.manager import ws_manager
import logging

logger = logging.getLogger(__name__)


@log_execution_block(title="Kafka Consumer - Handler")
async def kafka_consumer_handler(message: dict):
    try:
        dispatcher = CommandDispatcher()
        return await dispatcher.dispatch(message)
    except Exception as e:
        logger.error("websocket broadcast: %s", str(e))
        await ws_manager.broadcast(
            dict(value=dict(answer=str(e), hits=[])), lambda x: True
        )
