# ============================================
# backend/agents/analyzer_agent.py
# ============================================
from langgraph.graph.state import StateGraph, END, CompiledStateGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from services.agents.tools import create_analysis_tools
import json
from schemas.agent import AnalyzerState
from services.llm.llm_provider import select_llm
from langchain_core.tools import Tool
from datetime import datetime
from typing import Dict, List


class DataAnalyzerAgent:
    """데이터 분석 LangGraph Agent"""

    def __init__(self, llm_model: str):
        self.llm = select_llm(llm_name=llm_model)
        self.tools: list[Tool] = create_analysis_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """LangGraph 워크플로우 구축"""
        workflow = StateGraph(AnalyzerState)

        # 노드 정의
        workflow.add_node("profile_data", self.profile_data)
        workflow.add_node("select_analysis", self.select_analysis_method)
        workflow.add_node("perform_analysis", self.perform_analysis)
        workflow.add_node("extract_insights", self.extract_insights)
        workflow.add_node("quality_check", self.quality_check)

        # 엣지 정의
        workflow.set_entry_point("profile_data")
        workflow.add_edge("profile_data", "select_analysis")
        workflow.add_edge("select_analysis", "perform_analysis")
        workflow.add_edge("perform_analysis", "extract_insights")
        workflow.add_edge("extract_insights", "quality_check")

        # 조건부 엣지 - 품질이 낮으면 다른 분석 시도
        workflow.add_conditional_edges(
            "quality_check",
            self.should_continue_analysis,
            {"continue": "select_analysis", "end": END},
        )

        return workflow.compile()

    def profile_data(self, state: AnalyzerState) -> AnalyzerState:
        """Step 1: 데이터 프로파일링"""
        collected_data = state.collected_data
        profile = {}

        for source_name, data_str in collected_data.items():
            try:
                data = json.loads(data_str)
                if isinstance(data, dict) and "sample" in data:
                    # CSV/Excel 데이터
                    profile[source_name] = {
                        "type": "tabular",
                        "rows": data.get("rows", 0),
                        "columns": data.get("columns", []),
                        "data_types": data.get("dtypes", {}),
                    }
                else:
                    # 텍스트 데이터
                    profile[source_name] = {"type": "text", "length": len(str(data))}
            except:
                profile[source_name] = {"type": "unknown"}

        state.data_profile = profile
        state.steps_log.append(
            {"step": "profile_data", "profile": profile, "status": "completed"}
        )

        return state

    def select_analysis_method(self, state: AnalyzerState) -> AnalyzerState:
        """Step 2: 분석 방법 선택"""
        idx = state.current_analysis_index
        profile = state.data_profile

        # 이미 시도한 분석 방법 확인
        tried_analyses = [
            log.get("plan", {}).get("selected_tool")
            for log in (state.steps_log or [])
            if log.get("step") == "select_analysis"
        ]

        # LLM에게 최적의 분석 방법 추천 요청
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "당신은 데이터 분석 전문가입니다."),
                (
                    "human",
                    """
데이터 프로파일: {profile}
요청된 분석 유형: {analysis_types}
사용 가능한 분석 도구: {tools}
이미 시도한 분석: {tried_analyses}

현재 수행할 최적의 분석 도구와 파라미터를 JSON 형식으로 추천해주세요.

응답 형식:
{{
    "selected_tool": "도구명",
    "reasoning": "선택 이유",
    "parameters": {{
        "data_source": "사용할 데이터 소스명",
        "analysis_type": "분석 유형",
        "options": {{}}
    }},
    "expected_insights": ["예상되는 인사이트1", "예상되는 인사이트2"]
}}
""",
                ),
            ]
        )

        tool_desc = "\n".join(
            [f"- {name}: {tool.description}" for name, tool in self.tool_map.items()]
        )

        response = self.llm.invoke(
            prompt.format_messages(
                profile=json.dumps(profile, ensure_ascii=False, indent=2),
                analysis_type=state.analysis_types or "일반 분석",
                tools=tool_desc,
                tried_analyses=tried_analyses,
            )
        )

        try:
            content = str(response.content)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            analysis_plan = json.loads(content.strip())

            state.messages.append(f"assiatant: {analysis_plan['selected_tool']}")
            state.analysis_results.update({"selected_plan": analysis_plan})
            state.steps_log.append(
                {
                    "step": "select_analysis",
                    "plan": analysis_plan,
                    "status": "complete",
                    "attempt": idx + 1,
                }
            )

            return state
        except Exception as e:
            # 파싱 실패 시 기본 분석 설정
            default_source = (
                list(state.collected_data.keys())[0] if state.collected_data else None
            )

            analysis_plan = {
                "selected_tool": "통계",
                "reasoning": f"기본 통계 분석을 수행합니다. (파싱 오류: {str(e)})",
                "parameters": {
                    "data_source": default_source,
                    "analysis_type": "descriptive",
                },
                "expected_insights": ["기본 통계량", "데이터 분포"],
            }

            new_step_log = {
                "step": "select_analysis",
                "error": str(e),
                "fallback": "basic_statistics",
                "plan": analysis_plan,
                "status": "completed_with_fallback",
            }

            state.messages.append(f"assiatant: 기본 분석 방법으로 폴백: {str(e)}")
            state.analysis_results.update({"selected_plan": analysis_plan})
            state.steps_log.append(new_step_log)

            return state

    def perform_analysis(self, state: AnalyzerState) -> AnalyzerState:
        """Step 3: 선택된 분석 수행"""
        selected = state.analysis_results.get("selected_plan", {})
        tool_name = selected.get("selected_tool")
        params = selected.get("parameters", {})

        # 도구 실행
        tool = self.tool_map.get(tool_name, None)
        if tool and tool.func is not None:
            # 데이터 준비
            data_source = params.get("data_source")
            if data_source and data_source in state.collected_data:
                data_input = state.collected_data[data_source]
            else:
                # 첫 번째 데이터 소스 사용
                data_input = (
                    list(state.collected_data.values())[0]
                    if state.collected_data
                    else "{}"
                )

            try:
                # 도구 실행
                result = tool.func(data_input, **params.get("options", {}))

                analysis_result = {
                    "tool": tool_name,
                    "result": result,
                    "parameters": params,
                    "timestamp": str(datetime.now()),
                    "status": "success",
                }

                new_step_log = {
                    "step": "perform_analysis",
                    "tool": tool_name,
                    "status": "completed",
                }

                state.analysis_results.update(
                    {f"analysis_{tool_name}": analysis_result}
                )
                state.messages.append(f"assistant: {tool_name} 분석 완료")
                state.steps_log.append(new_step_log)
                return state

            except Exception as e:
                analysis_result = {
                    "tool": tool_name,
                    "error": str(e),
                    "parameters": params,
                    "status": "failed",
                }

                new_step_log = {
                    "step": "perform_analysis",
                    "tool": tool_name,
                    "error": str(e),
                    "status": "failed",
                }

                state.messages.append(f"assiatant: {tool_name} 분석 실패: {str(e)}")
                state.analysis_results.update(
                    {f"analysis_{tool_name}": analysis_result}
                )
                state.steps_log.append(new_step_log)
        else:
            new_step_log = {
                "step": "perform_analysis",
                "error": f"Tool {tool_name} not found",
                "status": "failed",
            }
            state.messages.append(f"assiatant: 도구를 찾을 수 없음: {tool_name}")
            state.steps_log.append(new_step_log)

        return state

    def extract_insights(self, state: AnalyzerState) -> AnalyzerState:
        """Step 4: 인사이트 추출"""
        analysis_results = state.analysis_results or {}

        # 최신 분석 결과 찾기
        latest_result = None
        for key, value in analysis_results.items():
            if key.startswith("analysis_") and isinstance(value, dict):
                if value.get("status") == "success":
                    latest_result = value
                    break

        if not latest_result:
            state.messages.append(f"assiatant: 분석 결과 없음")
            state.steps_log.append({"step": "extract_insights", "status": "no_results"})
            state.insights = ["분석 결과가 없습니다."]

            return state

        # LLM을 사용한 인사이트 추출
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "당신은 데이터 분석 결과를 해석하는 전문가입니다."),
                (
                    "human",
                    """
분석 도구: {tool}
분석 결과: {result}

위 분석 결과에서 핵심 인사이트를 3-5개 추출해주세요.
각 인사이트는 구체적이고 실행 가능한 형태로 작성해주세요.

응답 형식:
1. [인사이트 1]
2. [인사이트 2]
3. [인사이트 3]
...
""",
                ),
            ]
        )

        chain = prompt | self.llm

        try:
            response = chain.invoke(
                {
                    "tool": latest_result.get("tool", "unknown"),
                    "result": json.dumps(
                        latest_result.get("result", {}), ensure_ascii=False, indent=2
                    ),
                }
            )

            # 인사이트 파싱
            insights = [
                line.strip()
                for line in str(response.content).split("\n")
                if line.strip()
                and (line.strip()[0].isdigit() or line.strip().startswith("-"))
            ]

            new_step_log = {
                "step": "extract_insights",
                "insights_count": len(insights),
                "status": "completed",
            }

            state.messages.append(f"assiatant: {len(insights)}개 인사이트 추출 완료")
            state.steps_log.append(new_step_log)
            state.insights = insights

            return state

        except Exception as e:
            new_step_log = {
                "step": "extract_insights",
                "error": str(e),
                "status": "failed",
            }

            state.messages.append(f"assiatant: 인사이트 추출 실패: {str(e)}")
            state.steps_log.append(new_step_log)
            state.insights = [f"인사이트 추출 중 오류: {str(e)}"]

            return state

    def quality_check(self, state: AnalyzerState) -> AnalyzerState:
        """Step 5: 품질 검사"""
        # 간단한 품질 점수 계산
        quality_score = 0
        max_score = 100

        analysis_results = state.analysis_results

        # 분석 결과 존재 여부 (40점)
        successful_analyses = sum(
            1
            for key, value in analysis_results.items()
            if key.startswith("analysis_") and value.get("status") == "success"
        )
        if successful_analyses > 0:
            quality_score += 40

        # 인사이트 개수 (30점)
        insights_count = len(state.insights)
        quality_score += min(30, insights_count * 10)

        # 데이터 프로파일 완성도 (30점)
        if state.data_profile:
            quality_score += 30

        new_step_log = {
            "step": "quality_check",
            "score": quality_score,
            "successful_analyses": successful_analyses,
            "insights_count": insights_count,
            "status": "completed",
        }

        state.messages.append(f"품질 점수: {quality_score}/100")
        state.steps_log.append(new_step_log)
        state.analysis_results.update({"quality_score": quality_score})

        return state

    def should_continue_analysis(self, state: AnalyzerState) -> str:
        """분석을 계속할지 결정"""
        quality_score = state.analysis_results.get("quality_score", 0)
        max_retries = 3
        current_attempts = len(
            [log for log in state.steps_log if log.get("step") == "perform_analysis"]
        )

        # 품질이 낮고 재시도 횟수가 남았으면 계속
        if quality_score < 70 and current_attempts < max_retries:
            return "continue"

        return "end"

    def analyze(
        self, collected_data: Dict[str, str], analysis_types: List[str]
    ) -> Dict:
        """분석 실행"""
        initial_state = AnalyzerState(
            collected_data=collected_data,
            analysis_types=analysis_types or [],
            messages=[],
            data_profile={},
            analysis_results={},
            insights=[],
            current_analysis_index=0,
            steps_log=[],
        )

        # 그래프 실행
        final_state = self.graph.invoke(initial_state)

        return {
            "profile": final_state["data_profile"],
            "results": final_state["analysis_results"],
            "insights": final_state["insights"],
            "quality_score": final_state["analysis_results"].get("quality_score", 0),
            "steps": final_state["steps_log"],
            "messages": [msg.content for msg in final_state.get("messages", [])],
        }
