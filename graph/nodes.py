"""LangGraph Node Definitions.

Đóng gói các node trong đồ thị trạng thái:
- Planning Layer: research_node, planner_node, human_approve_plan_node
- Text Pipeline: outline_node, writer_node, review_node, factcheck_node, repurpose_node, carousel_node
- Convergence: join_node
"""

from typing import Dict, Any
from langgraph.types import interrupt
from core.state import ContentOSState

# Planning Layer Nodes
from agents.planning.research_agent import research_node
from agents.planning.planner_agent import planner_node

# Text Pipeline Nodes
from agents.text_pipeline.outline_agent import outline_node
from agents.text_pipeline.writer_agent import writer_node
from agents.text_pipeline.review_agent import review_node
from agents.text_pipeline.factcheck_agent import factcheck_node
from agents.text_pipeline.repurpose_agent import repurpose_node
from agents.text_pipeline.carousel_agent import carousel_node


def human_approve_plan_node(state: ContentOSState) -> Dict[str, Any]:
    """Human Touchpoint 1: Duyệt Kế hoạch tuần.
    
    Tạm dừng StateGraph qua interrupt(), hiển thị bản kế hoạch cho User.
    User gửi quyết định qua Command(resume={"approved": True/False, "note": "..."}).
    """
    content_plan = state.get("content_plan", [])
    week_id = state.get("week_id", "")

    # Payload ngắt gửi ra ngoài cho User giao tiếp
    interrupt_payload = {
        "touchpoint": 1,
        "action": "human_approve_plan",
        "week_id": week_id,
        "total_posts": len(content_plan),
        "content_plan": content_plan,
        "instruction": "Vui lòng xem xét ma trận kế hoạch tuần. Phê duyệt (approved=True) hoặc từ chối (approved=False kèm note).",
    }

    # Điểm ngắt Human-in-the-loop
    user_response = interrupt(interrupt_payload)

    # Xử lý phản hồi từ User
    if isinstance(user_response, dict):
        is_approved = bool(user_response.get("approved", False))
        revision_note = user_response.get("note")
    elif isinstance(user_response, bool):
        is_approved = user_response
        revision_note = None
    else:
        is_approved = False
        revision_note = str(user_response)

    # Tự động chọn bài viết đầu tiên làm topic nếu được duyệt
    selected_topic = content_plan[0] if (is_approved and content_plan) else {}

    return {
        "plan_approved": is_approved,
        "user_revision_note": revision_note,
        "selected_topic": selected_topic,
    }


def join_node(state: ContentOSState) -> Dict[str, Any]:
    """Node hội tụ các nhánh xử lý (Text Pipeline & Visual Pipeline)."""
    return {}
