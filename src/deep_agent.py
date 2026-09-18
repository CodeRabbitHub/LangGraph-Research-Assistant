from langgraph.graph import StateGraph, START, END
from src.utils.states import ResearchGraphState, ResearchGraphInput
from src.utils.nodes import (
    create_analysts,
    human_feedback,
    write_report,
    write_introduction,
    write_conclusion,
    finalize_report
)
from src.answering_questions import interview_builder
from src.utils.edges import initiate_all_interviews

# 1. Initialize master StateGraph with dedicated user input_schema
builder = StateGraph(ResearchGraphState, input_schema=ResearchGraphInput)

# 2. Add Nodes
builder.add_node("create_analysts", create_analysts)
builder.add_node("human_feedback", human_feedback)

# Subgraph as a node: the compiled interview graph is embedded directly
builder.add_node("conduct_interview", interview_builder.compile())

# Synthesis Nodes
builder.add_node("write_report", write_report)
builder.add_node("write_introduction", write_introduction)
builder.add_node("write_conclusion", write_conclusion)
builder.add_node("finalize_report", finalize_report)

# 3. Connect Flow
# Entry -> Create analyst personas -> Human feedback interrupt
builder.add_edge(START, "create_analysts")
builder.add_edge("create_analysts", "human_feedback")

# Map Step: Conditional Edge using Send() API to fan out parallel interviews
builder.add_conditional_edges(
    "human_feedback",
    initiate_all_interviews,
    ["create_analysts", "conduct_interview"]
)

# Fan-out: When interviews finish, run intro, body, and conclusion writers concurrently
builder.add_edge("conduct_interview", "write_report")
builder.add_edge("conduct_interview", "write_introduction")
builder.add_edge("conduct_interview", "write_conclusion")

# Fan-in Barrier (Join): Wait for all three synthesis nodes before assembling the final report
builder.add_edge(
    ["write_conclusion", "write_report", "write_introduction"],
    "finalize_report"
)
builder.add_edge("finalize_report", END)

# 4. Compile the complete Graph
# Note: In-node interrupt() inside human_feedback handles user input cleanly
graph = builder.compile()
