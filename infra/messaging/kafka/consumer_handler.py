from services.dispatchers.command_dispatcher import CommandDispatcher
from utils.logging import log_execution_block


@log_execution_block(title="Kafka Consumer - Handler")
async def kafka_consumer_handler(message: dict):
    dispatcher = CommandDispatcher()
    return await dispatcher.dispatch(message)
