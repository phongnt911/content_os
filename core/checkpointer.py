"""LangGraph Checkpointer Management.

Provides:
- In-memory checkpointer (`MemorySaver`) for LangGraph state persistence and interrupt/resume support.
- Configurable checkpointer factory.
"""

from typing import Any
from langgraph.checkpoint.memory import MemorySaver


def get_checkpointer(checkpointer_type: str = "memory") -> Any:
    """Trả về checkpointer instance tương thích với LangGraph StateGraph.
    
    Args:
        checkpointer_type: "memory" (mặc định)
    """
    # Mặc định sử dụng MemorySaver hỗ trợ đầy đủ interrupt & resume
    return MemorySaver()
