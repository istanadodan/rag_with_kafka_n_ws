import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
import logging
import cmn.event_loop as el
from services.kafka_handlers import BaseHandler
from utils.websocket_utils import ws_manager
from typing import Callable, Union

logger = logging.getLogger(__name__)


# 적재와 통지를 쓰레드에서 처리
class ThreadExecutor:

    def __init__(self, task: Union[BaseHandler, Callable]):
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._loop = el.MAIN_LOOP
        self._task = task if isinstance(task, Callable) else task.handle

    def submit(self, message: dict | None = None) -> Future:
        if self._loop is None:
            raise RuntimeError("Main loop not initialized.")

        # thread에 대한 future객체를 반환
        return self._executor.submit(self._thread_task, self._loop, message or {})

    def shutdown(self):
        self._executor.shutdown(wait=True)

    def _thread_task(self, loop, message: dict):
        # 1 blocking 작업처리
        logger.info("Received message: %s and call service", message)
        self._task(message)

        # 2 완료 후 websocket broadcast (event loop로 호출)
        # logger.info("websocket broadcast: %s", message)
        # asyncio.run_coroutine_threadsafe(
        #     ws_manager.broadcast(
        #         dict(value=f"{message}: upload complete"),
        #         lambda x: True,
        #     ),
        #     loop,
        # )
