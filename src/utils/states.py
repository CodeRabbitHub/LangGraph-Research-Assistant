import operator
from typing import List, Optional
from typing_extensions import Annotated, NotRequired, TypedDict
from langgraph.graph import MessagesState
from src.utils.objects import Analyst, SearchQuery


class GenerateAnalystsState(TypedDict):
    """State for Graph #1: Creating analyst personas and handling human feedback."""
    topic: str                                         # Research topic provided by user
    max_analysts: int                                  # Target number of analysts to generate
    human_analyst_feedback: NotRequired[Optional[str]] # Editorial feedback from human review
    analysts: NotRequired[List[Analyst]]               # Generated Analyst personas


class InterviewState(MessagesState):
    """
    State for Graph #2: Single analyst-expert interview loop.
    Inherits MessagesState, giving it a 'messages' key with the built-in add_messages reducer.
    """
    max_num_turns: int                     # Maximum Q&A turns allowed
    context: Annotated[list, operator.add] # Retrieved documents (accumulates over turns)
    analyst: Analyst                       # The persona assigned to this interview
    interview: str                         # Serialized text transcript of the interview
    sections: list                         # Output memo section written from this interview


class ResearchGraphState(TypedDict):
    """
    State for Graph #3: Full hierarchical research workflow.
    Coordinates persona generation, parallel fan-out interviews, and report synthesis.
    """
    topic: str                                         # Research topic
    max_analysts: int                                  # Number of analysts
    human_analyst_feedback: NotRequired[Optional[str]] # Editorial feedback from human
    analysts: List[Analyst]                            # List of confirmed analysts
    sections: Annotated[list, operator.add]            # Reduced list of all analyst memos
    introduction: str                                  # Generated report introduction
    content: str                                       # Generated report body (Insights)
    conclusion: str                                    # Generated report conclusion
    final_report: str                                  # Complete assembled Markdown report
