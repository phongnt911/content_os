"""LangGraph StateGraph Workflow Assembly & Compilation.

Biên dịch đồ thị trạng thái Cyclic StateGraph hoàn chỉnh cho POTA Content OS:
- Chặng 1: Planning Layer & Human Touchpoint 1 (Duyệt Plan tuần)
- Chặng 2A: Text Pipeline & Vòng lặp tự sửa bài (Self-Correction Loop: score < 8, max 2 lần)
- Chặng 2B: Visual Pipeline & Human Touchpoint 2 (Quay Video Raw) & Vòng lặp render lại (max 1 lần)
- Hội tụ song song tại `join_node` (DAG Fork-Join)
- Chặng 3: Human Touchpoint 3 (Duyệt trọn gói Final Package & Loop Breaker max 4 vòng)
- Chặng 4: Operations Layer (Xuất bản đa kênh -> Quản lý bình luận & CTA -> Đo lường & Cập nhật Brand Rules)
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
    # Operations & Human Touchpoint 3
    human_approve_final_package_node,
    publisher_node,
    community_node,
    analytics_node,
)
from graph.edges import (
    route_after_plan_approval,
    route_after_text_review,
    route_after_video_review,
    route_after_final_approval,
)


def create_content_os_graph(checkpointer: Optional[Any] = None) -> Any:
    """Khởi tạo và biên dịch StateGraph cho POTA Content OS đầy đủ 16 Agent & 3 Human Touchpoints."""
    builder = StateGraph(ContentOSState)

    # 1. Planning Layer Nodes (Chặng 1)
    builder.add_node("research", research_node)
    builder.add_node("planner", planner_node)
    builder.add_node("human_approve_plan", human_approve_plan_node)

    # 2. Text Pipeline Nodes (Chặng 2A)
    builder.add_node("generate_outline", outline_node)
    builder.add_node("writer", writer_node)
    builder.add_node("review_text", review_node)
    builder.add_node("fact_check", factcheck_node)
    builder.add_node("repurpose_threads", repurpose_node)
    builder.add_node("generate_carousel", carousel_node)

    # 3. Visual Pipeline Nodes (Chặng 2B)
    builder.add_node("generate_video_script", script_node)
    builder.add_node("human_record_video", human_record_video_node)
    builder.add_node("video_editing", video_editing_node)
    builder.add_node("review_video", review_video_node)
    builder.add_node("generate_cover_image", cover_agent_node)
    builder.add_node("review_image", review_image_node)

    # 4. Convergence Node (Hội tụ 2 nhánh song song)
    builder.add_node("join_node", join_node)

    # 5. Final Package Touchpoint & Operations Nodes (Chặng 3 & 4)
    builder.add_node("human_approve_final_package", human_approve_final_package_node)
    builder.add_node("publisher", publisher_node)
    builder.add_node("comment_manager", community_node)
    builder.add_node("analytics_learner", analytics_node)

    # 6. Planning Flow & Human Touchpoint 1
    builder.add_edge(START, "research")
    builder.add_edge("research", "planner")
    builder.add_edge("planner", "human_approve_plan")

    # 7. Fork song song sau Touchpoint 1 (Duyệt Plan)
    builder.add_conditional_edges(
        "human_approve_plan",
        route_after_plan_approval,
        [
            "generate_outline",
            "generate_video_script",
            END,
        ],
    )

    # 8. Nhánh A: Dây chuyền Chữ (Text Pipeline)
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

    # 9. Nhánh B: Dây chuyền Video & Ảnh (Visual Pipeline)
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

    # 10. Hội tụ dữ liệu và chuyển sang Human Touchpoint 3
    builder.add_edge("join_node", "human_approve_final_package")

    # 11. Conditional Edge sau Human Touchpoint 3 (Duyệt trọn gói)
    builder.add_conditional_edges(
        "human_approve_final_package",
        route_after_final_approval,
        {
            "publisher": "publisher",
            "generate_outline": "generate_outline",
            "generate_video_script": "generate_video_script",
            END: END,
        },
    )

    # 12. Operations Flow: Xuất bản -> Quản lý bình luận -> Đo lường học máy -> Hoàn tất (END)
    builder.add_edge("publisher", "comment_manager")
    builder.add_edge("comment_manager", "analytics_learner")
    builder.add_edge("analytics_learner", END)

    # 13. Compile StateGraph với checkpointer
    saver = checkpointer if checkpointer is not None else get_checkpointer()
    app = builder.compile(checkpointer=saver)
    return app


def get_compiled_app() -> Any:
    """Singleton getter trả về app đã compile sẵn."""
    return create_content_os_graph()
