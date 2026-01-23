from langchain_openai import ChatOpenAI
from core.config import settings
from langchain_core.tools import Tool
from services.agents.tools import create_data_collection_tools
from langgraph.graph.state import StateGraph, CompiledStateGraph, END
from schemas.agent import CollectorState, StateGraphInterface
from utils.logging import get_logger, log_execution_block
from langchain_core.prompts import ChatPromptTemplate

logger = get_logger(__name__)


class DataCollectorAgent:
    def __init__(self, llm_model: str | None = None):
        from services.llm.llm_provider import select_llm

        self.llm = select_llm(llm_name=llm_model or settings.llm_model_name)
        self.tools: list[Tool] = create_data_collection_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(CollectorState)
        workflow.add_node("check_source", self.check_data_source)
        workflow.add_node("select_tool", self.select_extraction_tool)
        workflow.add_node("extract_data", self.extract_data)
        workflow.add_node("validate_data", self.validate_data)

        workflow.set_entry_point("check_source")
        workflow.add_edge("check_source", "select_tool")
        workflow.add_edge("select_tool", "extract_data")
        workflow.add_edge("extract_data", "validate_data")
        workflow.add_conditional_edges(
            "validate_data",
            self.should_continue_collection,
            {
                "continue": "check_source",
                "end": END,
            },
        )
        return workflow.compile()

    # 입력데이터 유효성체크 후 다음스텝으로 넘김
    # 유효성오류인 경우,
    @log_execution_block("Agent:check_data_source")
    def check_data_source(self, state: CollectorState):
        """Step1: 현재 데이터 소스확인"""
        idx = state.current_source_index
        sources = state.data_sources
        if idx >= len(sources):
            return state
        current_source = sources[idx]
        state.steps_log.append(
            {"step": "check_source", "source": current_source, "satus": "completed"}
        )
        return state

    @log_execution_block("Agent:select_extraction_tool")
    def select_extraction_tool(self, state: CollectorState):
        """Step2: 저절한 추출 도구 선택"""

        source_type = state.data_sources[state.current_source_index].get(
            "source_type", ""
        )
        source_path = state.data_sources[state.current_source_index].get("path", "")
        prompt = ChatPromptTemplate(
            [
                (
                    "system",
                    "당신은 데이터 소스 타입에 맞는 도구를 선택하는 전문가입니다.",
                ),
                (
                    "human",
                    """
데이터 소스 정보:
- 타입: {source_type}
- 경로/URL: {source_path}

사용 가능한 도구:
{tools}

가장 적합한 도구명은 무엇인가요? 
생각한 내용중에 도구명만 추출해 반환하세요.
""",
                ),
            ]
        )
        tool_desc = "\n".join(
            [f"- {name}: {tool.description}" for name, tool in self.tool_map.items()]
        )

        response = self.llm.invoke(
            prompt.format_messages(
                source_type=source_type, source_path=source_path, tools=tool_desc
            )
        )
        selected_tool = (
            response.content.strip()
            if isinstance(response.content, str)
            else "Not_Found"
        )

        state.messages.append(f"assistant: {selected_tool}")
        state.steps_log.append(
            {"step": "select_tool", "tool": selected_tool, "status": "completed"}
        )
        return state

    @log_execution_block("Agent:extract_data")
    def extract_data(self, state: CollectorState):
        """Step3: 툴을 사용해서 파싱"""
        logger.info(f"Extracting data using {state}")
        print(f"Using tool: {state}")
        idx = state.current_source_index
        source = state.data_sources[idx]
        source_name = source.get("name", f"source_{idx}")

        tool_name = state.steps_log[-1].get("tool", "")
        # 호출 함수 매핑
        tool = self.tool_map.get(tool_name, None) or list(self.tool_map.values())[0]
        result = ""
        if tool and hasattr(tool, "func") and tool.func:
            try:
                path_or_url = source.get("path", source.get("url", ""))
                result = tool.func(path_or_url)
                state.collected_data[source_name] = result
                state.steps_log.append(
                    {
                        "step": "extract_data",
                        "status": "completed",
                        "preview": result[:500],
                    }
                )
            except Exception as e:
                state.errors.append(f"source {idx}: {str(e)}")
                state.steps_log.append(
                    {
                        "step": "extract_data",
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return state

    @log_execution_block("Agent:validate_data")
    def validate_data(self, state: CollectorState):
        """Step4: 추출된 데이터 검증"""
        idx = state.current_source_index
        source_name = state.data_sources[idx].get("name", f"source_{idx}")

        if source_name in state.collected_data:
            collected_data = state.collected_data[source_name]

            # LLM을 사용하여 데이터 품질 검증
            prompt = ChatPromptTemplate(
                [
                    (
                        "system",
                        "당신은 데이터 품질을 검증하는 전문가입니다.",
                    ),
                    (
                        "human",
                        """
다음은 추출된 데이터입니다:
{data_preview}

다음 기준으로 평가하세요:
1. 데이터가 유효한가?
2. 필요한 정보가 포함되어 있는가?
3. 품질 점수 (1-10)

검증 결과는 JSON 형식으로 답변해주세요:
{{
  "is_valid": true/false,
  "score": 1-10
  "issues": ["문제점1", "문제점2", ...]
}}
""",
                    ),
                ]
            )

            resonse = self.llm.invoke(
                prompt.format_messages(data_preview=collected_data[:500])
            )
            state.steps_log.append(
                {
                    "step": "validate_data",
                    "status": "completed",
                    "validation_response": str(resonse.content),
                }
            )

        # 다음 소스로 이동
        state.current_source_index += 1
        return state

    def should_continue_collection(self, state: CollectorState) -> str:
        if state.current_source_index >= len(state.data_sources):
            return "end"
        return "continue"

    def run(self, data_sources: list[dict]) -> dict:
        """Agent 실행"""
        initiaL_state = CollectorState(data_sources=data_sources)
        final_state = self.graph.invoke(initiaL_state)
        return {
            "collected_data": final_state["collected_data"],
            "steps": final_state["steps_log"],
            "errors": final_state["errors"],
        }


if __name__ == "__main__":
    agent: StateGraphInterface = DataCollectorAgent(llm_model="openai")
    r = agent.run(
        data_sources=[
            {
                "source_0": "LG계약서",
                "source_type": "pdf",
                "path": r"D:\mDocuments\구직활동\계약서\2025_LG엔솔_(주)윈스_프리랜서 표준계약서(권대영)_(2025.08.14).pdf",
            }
        ]
    )
    print(r)
