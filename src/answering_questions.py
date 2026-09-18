from langgraph.graph import StateGraph, START, END
from src.utils.states import InterviewState
from src.utils.nodes import (
    generate_question,
    generate_answer,
    save_interview,
    write_section
)
from src.utils.tools import search_web, search_web2
from src.utils.edges import route_messages

# 1. Initialize StateGraph with the InterviewState schema
interview_builder = StateGraph(InterviewState)

# 2. Add Nodes
interview_builder.add_node("ask_question", generate_question)
interview_builder.add_node("search_web", search_web)
interview_builder.add_node("search_web2", search_web2)
interview_builder.add_node("answer_question", generate_answer)
interview_builder.add_node("save_interview", save_interview)
interview_builder.add_node("write_section", write_section)

# 3. Flow Logic
# Begin by asking the first persona-grounded question
interview_builder.add_edge(START, "ask_question")

# Parallel search fan-out: both search_web and search_web2 run concurrently
interview_builder.add_edge("ask_question", "search_web")
interview_builder.add_edge("ask_question", "search_web2")

# Both searches converge back into answer_question
interview_builder.add_edge("search_web", "answer_question")
interview_builder.add_edge("search_web2", "answer_question")

# Conditional edge: either loop back to ask another question or finish & save
interview_builder.add_conditional_edges(
    "answer_question",
    route_messages,
    ["ask_question", "save_interview"]
)

# After saving interview, write the memo section and finish
interview_builder.add_edge("save_interview", "write_section")
interview_builder.add_edge("write_section", END)

# 4. Compile graph
question_answer_graph = interview_builder.compile()
