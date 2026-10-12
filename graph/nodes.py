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

    selected_topic: Dict[str, Any] = {}
    if is_approved:
        if isinstance(user_response, dict) and user_response.get("custom_topic"):
            c_topic = user_response["custom_topic"]
            if isinstance(c_topic, dict):
                selected_topic = c_topic
            else:
                selected_topic = {
                    "id": "post_custom",
                    "angle": str(c_topic),
                    "hook_concept": f"Ý tưởng mở bài cho: {c_topic}",
                    "target_channel": "Facebook",
                    "core_message": str(c_topic),
                }
        elif isinstance(user_response, dict) and "selected_index" in user_response:
            try:
                idx = int(user_response["selected_index"])
                if 0 <= idx < len(content_plan):
                    selected_topic = content_plan[idx]
                elif content_plan:
                    selected_topic = content_plan[0]
            except (ValueError, TypeError):
                selected_topic = content_plan[0] if content_plan else {}
        elif state.get("selected_topic") and state["selected_topic"].get("angle"):
            selected_topic = state["selected_topic"]
        elif content_plan:
            selected_topic = content_plan[0]

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


# Convergence Node
def join_node(state: ContentOSState) -> Dict[str, Any]:
    """Node hội tụ dữ liệu của 2 nhánh Text Pipeline & Visual Pipeline."""
    current_cycles = state.get("total_cycle_count", 0)
    return {
        "total_cycle_count": current_cycles + 1
    }


def human_approve_final_package_node(state: ContentOSState) -> Dict[str, Any]:
    """Human Touchpoint 3: Duyệt Trọn Gói Giao Phẩm Trước Khi Xuất Bản.
    
    Tạm dừng luồng bằng interrupt(), hiển thị đầy đủ payload gói nội dung:
    - Bài viết Facebook hoàn thiện
    - Chuỗi bài Threads
    - Slide Carousel
    - Link Video Render kèm thời lượng
    - Link Ảnh Bìa Cover
    - Số chu kỳ đã lặp (total_cycle_count)
    
    User gửi quyết định qua Command(resume={"approved": True/False, "note": "...", "revision_target": "text"|"video"}).
    """
    total_cycle_count = state.get("total_cycle_count", 1)

    preview_payload = {
        "touchpoint": 3,
        "action": "human_approve_final_package",
        "cycle_count": total_cycle_count,
        "max_cycles_allowed": 4,
        "topic": state.get("selected_topic", {}),
        "text_draft": state.get("fact_checked_draft") or state.get("raw_draft", ""),
        "threads_posts": state.get("threads_posts", []),
        "carousel_slides_count": len(state.get("carousel_slides", [])),
        "rendered_video_url": state.get("rendered_video_url"),
        "video_duration_seconds": state.get("video_duration", 0),
        "cover_image_url": state.get("cover_image_url"),
        "instruction": "Xem xét toàn bộ gói nội dung. Phê duyệt xuất bản (approved=True) hoặc yêu cầu chỉnh sửa (approved=False kèm note).",
    }

    user_response = interrupt(preview_payload)

    if isinstance(user_response, dict):
        is_approved = bool(user_response.get("approved", False))
        revision_note = user_response.get("note")
    elif isinstance(user_response, bool):
        is_approved = user_response
        revision_note = None
    else:
        is_approved = False
        revision_note = str(user_response)

    updates: Dict[str, Any] = {
        "final_package_approved": is_approved,
    }
    if revision_note is not None:
        updates["user_revision_note"] = revision_note

    return updates


# Operations Layer Nodes
from agents.operations.publisher_agent import publisher_node
from agents.operations.community_agent import community_node
from agents.operations.analytics_agent import analytics_node
