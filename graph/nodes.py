"""LangGraph Node Definitions.

Đóng gói các node trong đồ thị trạng thái:
- Node 1: research_node (Agent 1)
- Node 2: planner_node (Agent 2)
- Node 3: human_approve_plan_node (Human Touchpoint 1 với interrupt())
- Node 4: plan_dispatch_node (Chuẩn bị payload cho các chặng tiếp theo)
"""

from typing import Dict, Any
from langgraph.types import interrupt
from core.state import ContentOSState
from agents.planning.research_agent import research_node
from agents.planning.planner_agent import planner_node


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

    return {
        "plan_approved": is_approved,
        "user_revision_note": revision_note,
    }


def plan_dispatch_node(state: ContentOSState) -> Dict[str, Any]:
    """Node kích hoạt sau khi kế hoạch tuần được phê duyệt.
    
    Chọn bài viết đầu tiên trong content_plan làm `selected_topic` để sẵn sàng
    truyền vào Chặng 2 (Text Pipeline & Visual Pipeline).
    """
    content_plan = state.get("content_plan", [])
    selected_topic = content_plan[0] if content_plan else {}
    return {
        "selected_topic": selected_topic
    }
