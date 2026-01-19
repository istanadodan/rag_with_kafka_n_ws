from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class SourcePayload:
    # source = 원본 텍스트(pageContent)
    page_content: str
    metadata: Dict[str, Any]


class SourceRepository:
    """
    '원본 텍스트(source)' 저장을 Qdrant payload에 두되,
    향후 RDB로 분리하기 쉽게 Repository 계층으로 추상화.
    """

    def build_payload(self, source: SourcePayload) -> Dict[str, Any]:
        return {
            "source": source.page_content,
            **source.metadata,
        }
