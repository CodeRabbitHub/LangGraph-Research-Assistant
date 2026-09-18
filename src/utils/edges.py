from typing import Literal
from langchain_core.messages import AIMessage
from src.utils.states import GenerateAnalystsState, InterviewState, ResearchGraphState


def should_continue(state: GenerateAnalystsState) -> Literal["create_analysts", "dummy"]:
    """
    Conditional Edge: Routes execution after human_feedback.
    - If editorial feedback was provided -> loops back to 'create_analysts'
    - If approved (no feedback) -> proceeds to 'dummy' (and then END)
    """
    human_analyst_feedback = state.get("human_analyst_feedback", None)

    if human_analyst_feedback:
        return "create_analysts"

    return "dummy"


def route_messages(state: InterviewState, name: str = "expert"):
    """
    Conditional Edge: Routes between asking another question or saving the interview.
    Terminates when:
    1. The expert has answered max_num_turns times.
    2. The analyst signals completion with 'Thank you so much for your help'.
    """
    messages = state["messages"]
    max_num_turns = state.get("max_num_turns", 2)

    # Count how many answers the expert has provided
    num_responses = len([
        m for m in messages
        if isinstance(m, AIMessage) and getattr(m, "name", None) == name
    ])

    if num_responses >= max_num_turns:
        return "save_interview"

    # Check if the last analyst question signaled completion
    if len(messages) >= 2:
        last_question = messages[-2]
        if hasattr(last_question, "content") and "Thank you so much for your help" in str(last_question.content):
            return "save_interview"

    return "ask_question"


def initiate_all_interviews(state: ResearchGraphState):
    """
    Conditional Edge / Map Step:
    - If editorial feedback was provided -> loops back to 'create_analysts'
    - Otherwise -> Uses LangGraph's Send() API to fan out one 'conduct_interview'
      subgraph execution per confirmed analyst in parallel!
    """
    from langgraph.types import Send
    from langchain_core.messages import HumanMessage

    human_analyst_feedback = state.get("human_analyst_feedback", None)
    if human_analyst_feedback:
        return "create_analysts"

    topic = state["topic"]
    return [
        Send(
            "conduct_interview",
            {
                "analyst": analyst,
                "messages": [
                    HumanMessage(content=f"So you said you were writing an article on {topic}?")
                ]
            }
        )
        for analyst in state.get("analysts", [])
    ]
