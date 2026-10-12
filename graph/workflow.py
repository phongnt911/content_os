"""LangGraph StateGraph Workflow Assembly & Compilation.

Biên dịch đồ thị trạng thái Cyclic StateGraph cho LinTech Content OS:
- Chặng 1: Planning Layer & Human Touchpoint 1
- Chặng 2A: Text Pipeline & Vòng lặp tự sửa bài (Self-Correction Loop: score < 8)
- Chặng 2B: Visual Pipeline & Human Touchpoint 2 (Quay Video Raw) & Vòng lặp render lại
- Hội tụ song song tại `join_node` (DAG Fork-Join)
"""

from typing import Optional, Any
from langgraph.graph import StateGraph, START, END
from core.state import ContentOSState
from core.checkpointer import get_checkpointer
from graph.nodes import (
    # Planning
    research_node,
    planner_node,
    human_approve_plan_node,
    # Text Pipeline
    outline_node,
    writer_node,
    review_node,
    factcheck_node,
    repurpose_node,
    carousel_node,
    # Visual Pipeline
    script_node,
    human_record_video_node,
    video_editing_node,
    review_video_node,
    cover_agent_node,
    review_image_node,
    # Convergence
    join_node,
)
from graph.edges import (
    route_after_plan_approval,
    route_after_text_review,
    route_after_video_review,
)


def create_content_os_graph(checkpointer: Optional[Any] = None) -> Any:
    """Khởi tạo và biên dịch StateGraph cho Content OS hoàn chỉnh 2 nhánh Text & Visual."""
    builder = StateGraph(ContentOSState)

    # 1. Planning Layer Nodes
    builder.add_node("research", research_node)
    builder.add_node("planner", planner_node)
    builder.add_node("human_approve_plan", human_approve_plan_node)

    # 2. Text Pipeline Nodes
    builder.add_node("generate_outline", outline_node)
    builder.add_node("writer", writer_node)
    builder.add_node("review_text", review_node)
    builder.add_node("fact_check", factcheck_node)
    builder.add_node("repurpose_threads", repurpose_node)
    builder.add_node("generate_carousel", carousel_node)

    # 3. Visual Pipeline Nodes
    builder.add_node("generate_video_script", script_node)
    builder.add_node("human_record_video", human_record_video_node)
    builder.add_node("video_editing", video_editing_node)
    builder.add_node("review_video", review_video_node)
    builder.add_node("generate_cover_image", cover_agent_node)
    builder.add_node("review_image", review_image_node)

    # 4. Convergence Node
    builder.add_node("join_node", join_node)

    # 5. Planning Edges
    builder.add_edge(START, "research")
    builder.add_edge("research", "planner")
    builder.add_edge("planner", "human_approve_plan")

    # 6. Fork song song sau Human Touchpoint 1 (Duyệt Plan)
    builder.add_conditional_edges(
        "human_approve_plan",
        route_after_plan_approval,
        [
            "generate_outline",
            "generate_video_script",
            END,
        ],
    )

    # 7. Nhánh A: Dây chuyền Chữ
    builder.add_edge("generate_outline", "writer")
    builder.add_edge("writer", "review_text")
    builder.add_conditional_edges(
        "review_text",
        route_after_text_review,
        {
            "writer": "writer",
            "fact_check": "fact_check",
        },
    )
    builder.add_edge("fact_check", "repurpose_threads")
    builder.add_edge("repurpose_threads", "generate_carousel")
    builder.add_edge("generate_carousel", "join_node")

    # 8. Nhánh B: Dây chuyền Video & Ảnh
    builder.add_edge("generate_video_script", "human_record_video")
    builder.add_edge("human_record_video", "video_editing")
    builder.add_edge("video_editing", "review_video")
    builder.add_conditional_edges(
        "review_video",
        route_after_video_review,
        {
            "video_editing": "video_editing",
            "generate_cover_image": "generate_cover_image",
        },
    )
    builder.add_edge("generate_cover_image", "review_image")
    builder.add_edge("review_image", "join_node")

    # 9. Tạm thời kết thúc tại END sau join_node (Phase 5 sẽ nối sang Touchpoint 3)
    builder.add_edge("join_node", END)

    # 10. Compile StateGraph với checkpointer
    saver = checkpointer if checkpointer is not None else get_checkpointer()
    app = builder.compile(checkpointer=saver)
    return app


def get_compiled_app() -> Any:
    """Singleton getter trả về app đã compile sẵn."""
    return create_content_os_graph()
