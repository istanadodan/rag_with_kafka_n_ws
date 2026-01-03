from typing import Any
from langchain.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI
from pydantic.types import SecretStr
from core.config import settings


class LLMProvider:
    def __init__(self):
        self._llm = ChatOpenAI(
            model="gpt-5-mini-2025-08-07",
            temperature=1,
            api_key=SecretStr(settings.openai_api_key),
        )

    @property
    def llm(self):
        return self._llm


class StudioLMProvider:
    def __init__(self):
        self._llm = ChatOpenAI(
            # model="TheBloke/deepseek-coder-6.7B-instruct-GGUF",
            model="teddylee777/Llama-3-Open-Ko-8B-Instruct-preview-gguf",
            base_url="http://host.docker.internal:11434/v1",
            api_key=SecretStr("lm-studio"),
            temperature=1,
        )

    @property
    def llm(self):
        return self._llm


llm_provider = StudioLMProvider()
