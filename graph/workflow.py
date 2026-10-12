"""LangGraph StateGraph Workflow Assembly & Compilation.

Biên dịch đồ thị trạng thái Cyclic StateGraph cho LinTech Content OS:
- Chặng 1: Planning Layer & Human Touchpoint 1
- Chặng 2A: Text Pipeline & Vòng lặp tự sửa bài (Self-Correction Loop: score < 8)
- Hội tụ tạm thời tại join_node -> END (sẵn sàng đón Media Pipeline ở Phase 4)
"""

from typing import Optional, Any
from langgraph.graph import StateGraph, START, END
from core.state import ContentOSState
from core.checkpointer import get_checkpointer
from graph.nodes import (
    research_node,
    planner_node,
    human_approve_plan_node,
    outline_node,
    writer_node,
    review_node,
    factcheck_node,
    repurpose_node,
    carousel_node,
    join_node,
)
from graph.edges import (
    route_after_plan_approval,
    route_after_text_review,
)


def create_content_os_graph(checkpointer: Optional[Any] = None) -> Any:
    """Khởi tạo và biên dịch StateGraph cho Content OS hoàn chỉnh Text Pipeline."""
    builder = StateGraph(ContentOSState)

    # 1. Thêm Planning Layer Nodes
    builder.add_node("research", research_node)
    builder.add_node("planner", planner_node)
    builder.add_node("human_approve_plan", human_approve_plan_node)

    # 2. Thêm Text Pipeline Nodes (Tên node không được trùng với key trong ContentOSState)
    builder.add_node("generate_outline", outline_node)
    builder.add_node("writer", writer_node)
    builder.add_node("review_text", review_node)
    builder.add_node("fact_check", factcheck_node)
    builder.add_node("repurpose_threads", repurpose_node)
    builder.add_node("generate_carousel", carousel_node)
    builder.add_node("join_node", join_node)

    # 3. Các Edge chặng Planning
    builder.add_edge(START, "research")
    builder.add_edge("research", "planner")
    builder.add_edge("planner", "human_approve_plan")

    # 4. Conditional Edge sau Human Touchpoint 1
    builder.add_conditional_edges(
        "human_approve_plan",
        route_after_plan_approval,
        {
            "generate_outline": "generate_outline",
            END: END,
        },
    )

    # 5. Text Pipeline Edges & Vòng lặp tự sửa bài
    builder.add_edge("generate_outline", "writer")
    builder.add_edge("writer", "review_text")

    # Vòng lặp tự sửa bài: nếu draft_score < 8 và text_revision_count < 2 quay lại writer
    builder.add_conditional_edges(
        "review_text",
        route_after_text_review,
        {
            "writer": "writer",
            "fact_check": "fact_check",
        },
    )

    # Chuỗi xử lý sau khi duyệt text
    builder.add_edge("fact_check", "repurpose_threads")
    builder.add_edge("repurpose_threads", "generate_carousel")
    builder.add_edge("generate_carousel", "join_node")
    builder.add_edge("join_node", END)

    # 6. Compile đồ thị với checkpointer
    saver = checkpointer if checkpointer is not None else get_checkpointer()
    app = builder.compile(checkpointer=saver)
    return app


def get_compiled_app() -> Any:
    """Singleton getter trả về app đã compile sẵn."""
    return create_content_os_graph()
