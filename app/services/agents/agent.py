from langchain_openai import ChatOpenAI
from core.config import settings
from langchain_core.tools import Tool
from services.agents.tools import get_collector_tools
from langgraph.graph.state import StateGraph, CompiledStateGraph, END
from schemas.agent import CollectorState, StateGraphInterface


class DataCollectorAgent:
    def __init__(self):
        # self.llm = ChatOpenAI(model=settings.llm_model_name, temperature=1.0)
        self.tools: list[Tool] = get_collector_tools()
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

    def check_data_source(self, state: CollectorState):
        print("check_data")
        return state

    def select_extraction_tool(self, state: CollectorState):
        print("select_tool")
        state.messages.append("select_tool")
        print(state)
        return state

    def extract_data(self, state: CollectorState):
        print("extract_data")
        # state.messages = []
        return state

    def validate_data(self, state: CollectorState):
        print("validate_data")
        state.current_source_index += 1
        # state.messages = []
        return state

    def should_continue_collection(self, state: CollectorState) -> str:
        if state.current_source_index >= len(state.data_sources):
            return "end"
        return "continue"

    def run(self, data_sources: list[dict]) -> dict:
        """Agent 실행"""
        # initiaL_state = {
        #     "data_sources": data_sources,
        #     "current_source_index": 0,
        #     "collected_data": {},
        #     "messages": [],
        #     "steps_log": [],
        #     "errors": [],
        # }
        initiaL_state = CollectorState(data_sources=data_sources)
        return self.graph.invoke(initiaL_state)


if __name__ == "__main__":
    agent: StateGraphInterface = DataCollectorAgent()
    r = agent.run(data_sources=[{"source_id": "test", "source_type": "test"}])
    print(r)
