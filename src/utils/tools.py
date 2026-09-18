from langchain_core.messages import SystemMessage
from langchain_tavily import TavilySearch
from src.utils.prompts import search_instructions
from src.utils.states import InterviewState
from src.utils.objects import SearchQuery
from src.utils.models import llm

# Initialize Tavily search tool (returns top 3 factual results with URLs)
tavily_search = TavilySearch(max_results=3)


def execute_web_search(state: InterviewState):
    """
    Helper function:
    1. Analyzes conversation history using LLM with structured output.
    2. Formulates an optimized web search query.
    3. Executes Tavily search and formats results into <Document href="..."> tags.
    """
    # 1. Generate optimized search query from conversation history
    structured_llm = llm.with_structured_output(SearchQuery)
    search_query: SearchQuery = structured_llm.invoke(
        [SystemMessage(content=search_instructions)] + state.get("messages", [])
    )

    query_text = search_query.search_query.strip() if search_query and search_query.search_query else ""
    if not query_text:
        return {"context": []}

    # 2. Query Tavily API
    data = tavily_search.invoke({"query": query_text})
    if isinstance(data, dict):
        search_docs = data.get("results", [])
    elif isinstance(data, list):
        search_docs = data
    else:
        search_docs = []

    # 3. Format into standardized XML Document blocks preserving citation URLs
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc.get("url", "")}"/>\n{doc.get("content", "")}\n</Document>'
            for doc in search_docs
            if isinstance(doc, dict) and doc.get("content")
        ]
    )

    # 4. Return context update (appends via operator.add reducer in InterviewState)
    return {"context": [formatted_search_docs] if formatted_search_docs else []}


def search_web(state: InterviewState):
    """
    Primary Web Retrieval Node for the interview graph.
    """
    return execute_web_search(state)


def search_web2(state: InterviewState):
    """
    Parallel Web Retrieval Node allowing concurrent search query exploration.
    """
    return execute_web_search(state)
