import streamlit as st
import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, Any
from core.config import settings

SUPABASE_DB_URL = st.secrets.get(
    "SUPABASE_DB_URL",
    "postgresql://postgres.[YOUR_PASSWORD]@db.[YOUR_PROJECT_REF].supabase.co:5432/postgres",
)

SUPABASE_URL = settings.SUPABASE


@st.cache_resource
def get_db_connection():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


async def subscribe_pipeline_completed(callback=None):
    """pipeline_completed pg_notify 채널 구독"""
    conn = None
    try:
        conn = await asyncpg.connect(SUPABASE_DB_URL)

        async def listen():
            await conn.add_listener(
                "pipeline_completed", callback or handle_pipeline_event
            )
            st.balloons()
            st.success("✅ pipeline_completed 채널 구독 시작")

        await listen()
        await asyncio.sleep(3600)  # 1시간 대기

    except asyncio.CancelledError:
        pass
    except Exception as e:
        st.error(f"❌ 구독 오류: {e}")
    finally:
        if conn:
            await conn.close()


def handle_pipeline_event(conn, pid, channel, payload):
    """pipeline_completed 이벤트 핸들러"""
    try:
        event_data = json.loads(payload)
        event = {
            "channel": channel,
            "id": event_data.get("id"),
            "content": (
                event_data.get("content", "")[:200] + "..."
                if len(event_data.get("content", "")) > 200
                else event_data.get("content", "")
            ),
            "meta": event_data.get("meta"),
            "created_at": event_data.get("created_at"),
            "received_at": datetime.now().isoformat(),
        }

        if "pipeline_events" not in st.session_state:
            st.session_state.pipeline_events = []

        st.session_state.pipeline_events.append(event)
        st.session_state.last_pipeline_event = event

        # 알림 및 재실행
        st.session_state.show_notification = True
        st.rerun()

    except json.JSONDecodeError:
        st.session_state.error_payload = payload
        st.rerun()


# Streamlit UI
st.title("🔄 Pipeline Completed 실시간 모니터링")

if st.button("🎯 pipeline_completed 구독 시작", type="primary"):
    st.session_state.subscription_active = True
    asyncio.create_task(subscribe_pipeline_completed())

if st.button("⏹️ 구독 중지"):
    st.session_state.subscription_active = False
    st.success("구독 중지됨")

# 알림 표시
if st.session_state.get("show_notification", False):
    st.success("🎉 새 Pipeline 완료 이벤트 수신!")
    st.session_state.show_notification = False

# 이벤트 리스트
if "pipeline_events" in st.session_state:
    events = st.session_state.pipeline_events[-10:]  # 최근 10개

    for event in reversed(events):
        with st.expander(f"ID: {event['id']} | {event['received_at'][:19]}"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Pipeline ID", event["id"])
                st.caption(f"생성: {event['created_at'][:19]}")
            with col2:
                st.text_area(
                    "Content Preview", event["content"], height=100, disabled=True
                )
                st.json({"meta": event["meta"]})

if "error_payload" in st.session_state:
    st.error("JSON 파싱 오류: " + st.session_state.error_payload)
    del st.session_state.error_payload
