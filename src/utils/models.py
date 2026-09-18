import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env
load_dotenv()

# Configurable model name with fallback
model_name = os.getenv("OPENAI_MODEL", "gpt-4o")

# Main LLM instance with temperature=0 for deterministic, factual research outputs
llm = ChatOpenAI(
    model=model_name,
    temperature=0
)
