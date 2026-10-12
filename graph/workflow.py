"""LangGraph StateGraph Workflow Assembly & Compilation.

Biên dịch đồ thị trạng thái Cyclic StateGraph cho LinTech Content OS:
- Giai đoạn Phase 2:
  START -> research -> plan -> human_approve_plan
  human_approve_plan --[approved=True]--> plan_dispatch -> END
  human_approve_plan --[approved=False]--> END
"""

from typing import Optional, Any
from langgraph.graph import StateGraph, START, END
from core.state import ContentOSState
from core.checkpointer import get_checkpointer
from graph.nodes import (
    research_node,
    planner_node,
    human_approve_plan_node,
    plan_dispatch_node,
)
from graph.edges import route_after_plan_approval


def create_content_os_graph(checkpointer: Optional[Any] = None) -> Any:
    """Khởi tạo và biên dịch StateGraph cho Content OS."""
    builder = StateGraph(ContentOSState)

    # 1. Thêm các Node
    builder.add_node("research", research_node)
    builder.add_node("plan", planner_node)
    builder.add_node("human_approve_plan", human_approve_plan_node)
    builder.add_node("plan_dispatch", plan_dispatch_node)

    # 2. Thêm các Edge cố định
    builder.add_edge(START, "research")
    builder.add_edge("research", "plan")
    builder.add_edge("plan", "human_approve_plan")

    # 3. Thêm Conditional Edge sau Human Touchpoint 1
    builder.add_conditional_edges(
        "human_approve_plan",
        route_after_plan_approval,
        {
            "plan_dispatch": "plan_dispatch",
            END: END,
        },
    )

    # 4. plan_dispatch tạm thời kết thúc tại END trong Phase 2 (sẽ nối sang Chặng 2 ở Phase 3 & 4)
    builder.add_edge("plan_dispatch", END)

    # 5. Compile với checkpointer để kích hoạt interrupt()
    saver = checkpointer if checkpointer is not None else get_checkpointer()
    app = builder.compile(checkpointer=saver)
    return app


def get_compiled_app() -> Any:
    """Singleton getter trả về app đã compile sẵn."""
    return create_content_os_graph()
