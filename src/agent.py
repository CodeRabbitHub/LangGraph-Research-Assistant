from langgraph.graph import StateGraph, START, END
from src.utils.states import GenerateAnalystsState
from src.utils.nodes import create_analysts, human_feedback, dummy
from src.utils.edges import should_continue

# Initialize the StateGraph with our typed state
builder = StateGraph(GenerateAnalystsState)

# 1. Add Nodes (the workers)
builder.add_node("create_analysts", create_analysts)
builder.add_node("human_feedback", human_feedback)
builder.add_node("dummy", dummy)

# 2. Add Edges (the connections)
builder.add_edge(START, "create_analysts")
builder.add_edge("create_analysts", "human_feedback")

# 3. Add Conditional Routing
# After human_feedback, should_continue checks if feedback was provided:
# -> If feedback exists: route back to "create_analysts"
# -> If approved: route to "dummy" -> END
builder.add_conditional_edges(
    "human_feedback",
    should_continue,
    ["create_analysts", "dummy"]
)
builder.add_edge("dummy", END)

# 4. Compile the Graph
# Note: In-node interrupt() inside human_feedback handles user input cleanly
graph = builder.compile()
