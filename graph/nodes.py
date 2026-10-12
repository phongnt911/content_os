"""LangGraph Node Definitions.

Đóng gói các node trong đồ thị trạng thái:
- Planning Layer: research_node, planner_node, human_approve_plan_node
- Text Pipeline: outline_node, writer_node, review_node, factcheck_node, repurpose_node, carousel_node
- Visual Pipeline: script_node, human_record_video_node, video_editing_node, review_video_node, cover_agent_node, review_image_node
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

# Visual Pipeline Nodes
from agents.media_pipeline.script_agent import script_node
from agents.media_pipeline.video_editor import video_editing_node
from agents.media_pipeline.review_video import review_video_node
from agents.media_pipeline.cover_agent import cover_agent_node
from agents.media_pipeline.review_image import review_image_node


def human_approve_plan_node(state: ContentOSState) -> Dict[str, Any]:
    """Human Touchpoint 1: Duyệt Kế hoạch tuần.
    
    Tạm dừng StateGraph qua interrupt(), hiển thị bản kế hoạch cho User.
    User gửi quyết định qua Command(resume={"approved": True/False, "note": "..."}).
    """
    content_plan = state.get("content_plan", [])
    week_id = state.get("week_id", "")

    interrupt_payload = {
        "touchpoint": 1,
        "action": "human_approve_plan",
        "week_id": week_id,
        "total_posts": len(content_plan),
        "content_plan": content_plan,
        "instruction": "Vui lòng xem xét ma trận kế hoạch tuần. Phê duyệt (approved=True) hoặc từ chối (approved=False kèm note).",
    }

    user_response = interrupt(interrupt_payload)

    if isinstance(user_response, dict):
        is_approved = bool(user_response.get("approved", False))
        revision_note = user_response.get("note")
    elif isinstance(user_response, bool):
        is_approved = user_response
        revision_note = None
    else:
        is_approved = False
        revision_note = str(user_response)

    selected_topic = content_plan[0] if (is_approved and content_plan) else {}

    return {
        "plan_approved": is_approved,
        "user_revision_note": revision_note,
        "selected_topic": selected_topic,
    }


def human_record_video_node(state: ContentOSState) -> Dict[str, Any]:
    """Human Touchpoint 2: Quay Clip.
    
    Tạm dừng luồng bằng interrupt() chờ User đọc kịch bản video, tự quay clip raw
    và nạp link Google Drive vào state (`raw_footage_url`).
    """
    video_script = state.get("video_script", {})

    interrupt_payload = {
        "touchpoint": 2,
        "action": "human_record_video",
        "hook_opening": video_script.get("hook_opening", ""),
        "total_scenes": len(video_script.get("scenes", [])),
        "video_script": video_script,
        "instruction": "Vui lòng đọc kịch bản trên, tự quay video thô và gửi link Google Drive / URL video vào.",
    }

    user_response = interrupt(interrupt_payload)

    if isinstance(user_response, dict):
        raw_footage_url = user_response.get("raw_footage_url") or user_response.get("url")
    elif isinstance(user_response, str):
        raw_footage_url = user_response
    else:
        raw_footage_url = None

    if not raw_footage_url:
        raw_footage_url = "https://drive.google.com/file/d/sample_creator_raw_footage/view"

    return {
        "raw_footage_url": raw_footage_url
    }


def join_node(state: ContentOSState) -> Dict[str, Any]:
    """Node hội tụ dữ liệu của 2 nhánh Text Pipeline & Visual Pipeline."""
    current_cycles = state.get("total_cycle_count", 0)
    return {
        "total_cycle_count": current_cycles + 1
    }
