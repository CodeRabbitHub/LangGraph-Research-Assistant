from langgraph.types import interrupt
from langchain_core.messages import SystemMessage, HumanMessage, get_buffer_string
from src.utils.states import GenerateAnalystsState, InterviewState, ResearchGraphState
from src.utils.objects import Perspectives, Analyst
from src.utils.models import llm
from src.utils.prompts import (
    analyst_instructions,
    question_instructions,
    answer_instructions,
    section_writer_instructions,
    report_writer_instructions,
    intro_conclusion_instructions
)


def create_analysts(state: GenerateAnalystsState):
    """
    Node: Generates diverse Analyst personas based on the topic and optional human feedback.
    Enforces structured output using the Pydantic Perspectives schema.
    """
    topic = state["topic"]
    max_analysts = state["max_analysts"]
    human_analyst_feedback = state.get("human_analyst_feedback", "") or ""

    # Enforce structured output via Pydantic schema
    structured_llm = llm.with_structured_output(Perspectives)

    # Format system prompt with topic, feedback, and target analyst count
    system_prompt = analyst_instructions.format(
        topic=topic,
        human_analyst_feedback=human_analyst_feedback,
        max_analysts=max_analysts
    )

    # Invoke LLM
    perspectives: Perspectives = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Generate the set of analysts.")
    ])

    # Return updated state key 'analysts'
    return {"analysts": perspectives.analysts}


def human_feedback(state: GenerateAnalystsState):
    """
    Node: Pauses graph execution using LangGraph's interrupt() function.
    Exposes the generated analysts to the human reviewer for approval or critique.
    """
    feedback = interrupt({
        "question": "Are these analysts acceptable?",
        "analysts": [
            analyst.model_dump() if hasattr(analyst, "model_dump") else analyst
            for analyst in state.get("analysts", [])
        ],
        "instructions": "Type feedback to regenerate with corrections, or type 'perfect' / 'continue' to approve."
    })

    # If no feedback or empty, treat as approval
    if not feedback:
        return {"human_analyst_feedback": None}

    if isinstance(feedback, str):
        clean_feedback = feedback.strip().lower()
        if clean_feedback in {"", "perfect", "continue", "approved", "yes", "y"}:
            return {"human_analyst_feedback": None}
        return {"human_analyst_feedback": feedback}

    return {"human_analyst_feedback": None}


def dummy(state: GenerateAnalystsState):
    """
    No-op node acting as a clean pass-through destination after approval before END.
    """
    return {}


def generate_question(state: InterviewState):
    """
    Node: Generates the analyst's interview question.
    Employs the persona and areas of focus defined for this specific analyst.
    """
    analyst = state["analyst"]
    if isinstance(analyst, dict):
        analyst = Analyst.model_validate(analyst)

    messages = state["messages"]

    # System prompt formatted with this analyst's persona goals
    system_prompt = question_instructions.format(goals=analyst.persona)
    question = llm.invoke([SystemMessage(content=system_prompt)] + messages)

    # Return updated conversation messages
    return {"messages": [question]}


def generate_answer(state: InterviewState):
    """
    Node: Expert persona answers the analyst's question.
    Answers strictly using retrieved web context and incorporates [1], [2] citations.
    """
    analyst = state["analyst"]
    if isinstance(analyst, dict):
        analyst = Analyst.model_validate(analyst)

    messages = state["messages"]
    context = state.get("context", [])

    system_prompt = answer_instructions.format(
        goals=analyst.persona,
        context=context
    )
    answer = llm.invoke([SystemMessage(content=system_prompt)] + messages)

    # Name the message as coming from the expert for turn-tracking
    answer.name = "expert"

    return {"messages": [answer]}


def save_interview(state: InterviewState):
    """
    Node: Serializes the full interview dialogue history into a plain text transcript.
    """
    from langchain_core.messages import get_buffer_string
    messages = state["messages"]
    interview_transcript = get_buffer_string(messages)
    return {"interview": interview_transcript}


def write_section(state: InterviewState):
    """
    Node: Synthesizes the interview and gathered context into a structured ~400-word memo section.
    """
    context = state.get("context", [])
    analyst = state["analyst"]
    if isinstance(analyst, dict):
        analyst = Analyst.model_validate(analyst)

    system_prompt = section_writer_instructions.format(focus=analyst.description)
    section = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Use this source to write your section:\n\n{context}")
    ])

    return {"sections": [section.content]}


def write_report(state: ResearchGraphState):
    """
    Node: Synthesizes all gathered analyst memos into a unified central narrative (## Insights).
    Preserves in-text [1], [2] citations and creates a consolidated ## Sources section.
    """
    sections = state.get("sections", [])
    topic = state["topic"]

    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])

    system_prompt = report_writer_instructions.format(
        topic=topic,
        context=formatted_str_sections
    )
    report = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Write a report based upon these memos.")
    ])

    return {"content": report.content}


def write_introduction(state: ResearchGraphState):
    """
    Node: Crafts a crisp, compelling introduction previewing all research angles.
    """
    sections = state.get("sections", [])
    topic = state["topic"]

    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    system_prompt = intro_conclusion_instructions.format(
        topic=topic,
        formatted_str_sections=formatted_str_sections
    )

    intro = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Write the report introduction")
    ])

    return {"introduction": intro.content}


def write_conclusion(state: ResearchGraphState):
    """
    Node: Crafts a crisp conclusion summarizing key implications and takeaways.
    """
    sections = state.get("sections", [])
    topic = state["topic"]

    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    system_prompt = intro_conclusion_instructions.format(
        topic=topic,
        formatted_str_sections=formatted_str_sections
    )

    conclusion = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Write the report conclusion")
    ])

    return {"conclusion": conclusion.content}


def finalize_report(state: ResearchGraphState):
    """
    Node: The 'Reduce' assembly step.
    Assembles introduction, core insights body, conclusion, and consolidated sources into the final Markdown report.
    """
    content = state.get("content", "")

    # Clean header prefix if present
    if content.startswith("## Insights"):
        content = content.replace("## Insights", "", 1).strip()

    sources = None
    if "## Sources" in content:
        try:
            content_part, sources_part = content.split("\n## Sources\n", 1)
            content = content_part.strip()
            sources = sources_part.strip()
        except Exception:
            sources = None

    # Assemble structured final document
    final_report = (
        state.get("introduction", "").strip()
        + "\n\n---\n\n## Insights\n\n"
        + content
        + "\n\n---\n\n"
        + state.get("conclusion", "").strip()
    )

    if sources:
        final_report += "\n\n---\n\n## Sources\n\n" + sources

    return {"final_report": final_report}
