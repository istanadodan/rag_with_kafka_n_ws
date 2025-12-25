from __future__ import annotations

from typing import Dict, Any, cast
import stomper
from schemas.stomp import StompFrameModel


def pars_stomp_text(raw: str) -> StompFrameModel:
    """
    stomper는 '프레임 생성/파싱' 기능을 제공하지만,
    실제 네트워크 송수신은 사용자가 담당하는 라이브러리입니다.
    """
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    frame: Dict[str, Any] = stomper.unpack_frame(raw)

    cmd = frame.get("cmd", "").upper()
    headers = frame.get("headers", {})
    body = frame.get("body", "")

    if not cmd:
        raise ValueError("Invalid STOMP frame: missing command")
    # headers값이 bytes일 수 있으니, 문자열로 정규화
    norm_headers: Dict[str, str] = {str(k): str(v) for k, v in headers.items()}
    return StompFrameModel(command=cmd, headers=norm_headers, body=str(body))


def build_frame(
    command: str, headers: Dict[str, str] | None = None, body: str = ""
) -> str:
    headers = headers or {}
    f = stomper.Frame()
    f.cmd = command.upper()
    cast(Dict, f.headers).update(headers)
    f.body = body
    # pack()은 \0종료 포함 STOMP문자열을 생성
    return f.pack()
