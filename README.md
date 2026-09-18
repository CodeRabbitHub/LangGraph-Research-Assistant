# LangGraph Multi-Agent Research Assistant

An autonomous, multi-agent research assistant built with **LangGraph**, **LangChain**, **OpenAI**, and **Tavily**.

Given a complex research topic, the system generates diverse expert analyst personas, pauses for **human editorial feedback**, executes **parallel multi-turn interviews** grounded in live web search, and synthesizes findings into an executive Markdown research report with verified source citations.

---

## Architecture Overview

```text
                                [ Research Topic ]
                                        │
                                        ▼
                             [ 1. create_analysts ]
                       (Generates N specialized expert personas)
                                        │
                                        ▼
                             [ 2. human_feedback ]
                     (⏸️ Pauses for your approval or critique)
                                        │
                    ┌───────────────────┴───────────────────┐
              (Feedback given)                        (Approved!)
                    │                                       │
                    ▼                                       ▼
          [ create_analysts ]                   [ initiate_all_interviews ]
                                                            │
                                         ┌──────────────────┴──────────────────┐
                                         │    LangGraph Send() API Fan-Out     │
                                         ▼                                     ▼
                            [ Interview Subgraph 1 ]              [ Interview Subgraph 2 ]
                            (Analyst asks questions,              (Analyst asks questions,
                             concurrent Tavily searches,           concurrent Tavily searches,
                             expert answers with [1] citations,    expert answers with [1] citations,
                             writes section memo)                  writes section memo)
                                         │                                     │
                                         └──────────────────┬──────────────────┘
                                                            │ (Collected via Reducer)
                                     ┌──────────────────────┼──────────────────────┐
                                     ▼                      ▼                      ▼
                               [write_intro]          [write_report]         [write_conclusion]
                                     └──────────────────────┬──────────────────────┘
                                                            │ (Fan-in Barrier / Join)
                                                            ▼
                                                    [finalize_report]
                                                            │
                                                            ▼
                                                    final_report.md
```

---

## Features

- **Hierarchical Multi-Agent Graph**: Coordinates high-level planning and low-level interview subgraphs using LangGraph's `Send()` API.
- **Human-in-the-Loop (`interrupt`)**: Halts execution before research starts, letting you inspect, critique, or approve the panel of analysts.
- **Grounded Web Search**: Extracts optimized queries from conversation state and fetches live facts via Tavily.
- **Strict Citation Contracts**: Enforces numbered in-text citations (`[1]`, `[2]`) linked directly to source URLs.
- **Map-Reduce Synthesis**: Reducers (`Annotated[list, operator.add]`) collect memos from parallel workers and synthesize them into a cohesive narrative.
- **LangSmith Tracing**: Full observability into LLM token usage, tool calls, and graph state transitions.
- **Two Ways to Run**: Interactive terminal CLI (`main.py`) or visual LangGraph Studio (`langgraph dev`).

---

## Project Structure

```text
LangGraph_Assistant/
├── main.py                     # Interactive CLI terminal runner
├── langgraph.json              # LangGraph Studio registry
├── pyproject.toml              # Dependencies and metadata
├── .env                        # Local API credentials (ignored by git)
├── .env.example                # Template for environment variables
└── src/
    ├── agent.py                # Graph #1: Analyst generator with human interrupt
    ├── answering_questions.py  # Graph #2: Analyst-Expert interview subgraph
    ├── deep_agent.py           # Graph #3: End-to-end Map-Reduce research graph
    └── utils/
        ├── models.py           # ChatOpenAI model setup
        ├── objects.py          # Pydantic schemas (Analyst, Perspectives, SearchQuery)
        ├── states.py           # LangGraph State schemas with reducers
        ├── prompts.py          # Prompt engineering contracts
        ├── tools.py            # Tavily web search integration
        ├── nodes.py            # Graph node implementations
        └── edges.py            # Conditional routing logic
```

---

## Quickstart

### 1. Configure Environment Variables
Create your `.env` file (copied from `.env.example`):

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
TAVILY_API_KEY=tvly-...

# LangSmith Observability (Optional)
LANGCHAIN_TRACING_V2=true
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=langgraph-research-assistant
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### 2. Option A: Run the Terminal CLI
Run the interactive research assistant directly from your terminal:

```bash
uv run python main.py
```
- Enter your research topic and analyst count.
- Review the proposed analysts right in your terminal.
- Type feedback to regenerate, or press **Enter** to approve.
- Watch parallel interviews stream, and find your generated report in `final_report.md`!

### 3. Option B: Run with LangGraph Studio
Launch the visual graph debugger and web UI:

```bash
uv run langgraph dev
```
Open the local URL displayed in your terminal to inspect graph state, visualize nodes, and step through checkpoints visually.

---

## Graphs in `langgraph.json`

| Graph ID | Entrypoint | Purpose |
|:---|:---|:---|
| `deep_agent` | `src/deep_agent.py:graph` | Full end-to-end research workflow (Map-Reduce) |
| `create_analysts` | `src/agent.py:graph` | Analyst persona generator and human approval loop |
| `answer_question` | `src/answering_questions.py:question_answer_graph` | Single analyst interview subgraph |
