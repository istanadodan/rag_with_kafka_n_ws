# from dataclasses import dataclass
# from typing import Optional, cast
# from langchain.agents import create_agent
# from langchain.agents.middleware import dynamic_prompt, ModelRequest
# from langchain.agents.middleware import AgentMiddleware


# @dataclass
# class Context:
#     user_role: str = "user"


# @dynamic_prompt
# def dynamic_prompt1(request: ModelRequest) -> str:
#     context = cast(Optional[Context], request.runtime.context)
#     user_role = context.user_role if context else "user"

#     base_prompt = "You are a helpful assistant."

#     if user_role == "expert":
#         return f"{base_prompt} Provide detailed technical responses."
#     elif user_role == "beginner":
#         return f"{base_prompt} Explain concepts simply and avoid jargon."
#     return base_prompt

# from typing import override

# class CustMiddleare(AgentMiddleware):

#     @override
#     def before_model(
#         self, state: AgentState, runtime: Runtime
#     ) -> dict[str, Any] | None:
#         """Process messages before model invocation, potentially triggering summarization."""
#         messages = state["messages"]
#         self._ensure_message_ids(messages)

#         total_tokens = self.token_counter(messages)
#         if not self._should_summarize(messages, total_tokens):
#             return None

#         cutoff_index = self._determine_cutoff_index(messages)

#         if cutoff_index <= 0:
#             return None

#         messages_to_summarize, preserved_messages = self._partition_messages(
#             messages, cutoff_index
#         )

#         summary = self._create_summary(messages_to_summarize)
#         new_messages = self._build_new_messages(summary)

#         return {
#             "messages": [
#                 RemoveMessage(id=REMOVE_ALL_MESSAGES),
#                 *new_messages,
#                 *preserved_messages,
#             ]
#         }

#     @override
#     async def abefore_model(
#         self, state: AgentState, runtime: Runtime
#     ) -> dict[str, Any] | None:
#         """Process messages before model invocation, potentially triggering summarization."""
#         messages = state["messages"]
#         self._ensure_message_ids(messages)

#         total_tokens = self.token_counter(messages)
#         if not self._should_summarize(messages, total_tokens):
#             return None

#         cutoff_index = self._determine_cutoff_index(messages)

#         if cutoff_index <= 0:
#             return None

#         messages_to_summarize, preserved_messages = self._partition_messages(
#             messages, cutoff_index
#         )

#         summary = await self._acreate_summary(messages_to_summarize)
#         new_messages = self._build_new_messages(summary)

#         return {
#             "messages": [
#                 RemoveMessage(id=REMOVE_ALL_MESSAGES),
#                 *new_messages,
#                 *preserved_messages,
#             ]
#         }


# middleware: list[AgentMiddleware | None] = [dynamic_prompt1]

# agent = create_agent(
#     model="gpt-5-mini-2025-08-07",
#     tools=[],
#     middleware=CustMiddleare(),
#     context_schema=Context,
# )

# agent.invoke(
#     {"messages": [{"role": "user", "content": "Explain async programming"}]},
#     context=Context(user_role="expert"),
# )

# from langchain.agents import create_agent
# from langchain.agents.middleware import SummarizationMiddleware

# agent = create_agent(
#     model="claude-sonnet-4-5-20250929",
#     tools=[],
#     middleware=[
#         SummarizationMiddleware(
#             model="claude-sonnet-4-5-20250929", max_tokens_before_summary=1000
#         )
#     ],
# )
