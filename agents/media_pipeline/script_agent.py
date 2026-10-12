"""Agent 9: Video Script Agent (Visual Pipeline).

Nhiệm vụ:
- Tiếp nhận `selected_topic` (hoặc bài viết từ `content_plan[0]`) và `brand_rules`.
- Soạn thảo kịch bản video ngắn dạng bảng (30-50s) cho TikTok/Reels/Shorts:
  + Thời lượng từng phân đoạn (giây).
  + Visual Cue (chỉ dẫn góc máy, động tác, hình ảnh minh họa).
  + Voice Prompter (lời thoại hiển thị trên máy nhắc chữ cho creator).
- Bắt buộc sử dụng `.with_structured_output(VideoScriptResult)` theo Rule 4.
- Cập nhật trường `video_script` trong ContentOSState.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, VideoScriptResult
from config import get_llm


SCRIPT_SYSTEM_PROMPT = """Bạn là Agent 9 (Short-form Video Screenwriter & Director) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Tiếp nhận chủ đề bài viết và các quy chuẩn thương hiệu (brand_rules).
2. Viết một kịch bản video ngắn (30 đến 50 giây) chuẩn định dạng dọc (9:16) cho TikTok / Facebook Reels / YouTube Shorts:
   - total_estimated_duration: Tổng thời lượng dự kiến từ 30 - 50 giây (bắt buộc < 60s).
   - hook_opening: Lời thoại hook giật tò mò trong 3 giây đầu tiên.
   - scenes: Danh sách các phân cảnh (scene_number, duration_seconds, visual_cue, voice_prompter).
   - cta_closing: Lời kêu gọi hành động cuối video (comment từ khóa để nhận tài liệu/workflow).
3. Visual Cue phải miêu tả chi tiết: góc máy (cận cảnh / trung cảnh), biểu cảm khuôn mặt, chuyển động tay, văn bản hiển thị trên màn hình.
4. Voice Prompter: Lời thoại tự nhiên, câu ngắn, nhịp điệu nhanh và tràn đầy năng lượng.

Bắt buộc trả về đúng cấu trúc VideoScriptResult."""


def run_script_agent(
    selected_topic: Dict[str, Any],
    brand_rules: List[str],
) -> VideoScriptResult:
    """Thực thi logic biên soạn kịch bản video của Agent 9 với structured output bắt buộc."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(VideoScriptResult)

    topic_id = selected_topic.get("id", "post_01")
    angle = selected_topic.get("angle", "Thực chiến tối ưu tự động hóa AI")
    hook_concept = selected_topic.get("hook_concept", "Sai lầm khiến bạn tốn hàng giờ làm video")
    core_message = selected_topic.get("core_message", "AI tự động hóa quy trình sản xuất video")
    rules_context = "\n- ".join(brand_rules) if brand_rules else "Phong cách chuyên gia gần gũi, thực tế, năng động."

    user_prompt = f"""Hãy viết kịch bản video ngắn 30-50s hoàn chỉnh cho chủ đề sau:
- Mã bài viết: {topic_id}
- Góc tiếp cận (Angle): {angle}
- Ý tưởng hook: {hook_concept}
- Thông điệp cốt lõi: {core_message}

Brand Rules:
- {rules_context}

Xuất ra cấu trúc VideoScriptResult chuẩn xác."""

    messages = [
        SystemMessage(content=SCRIPT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    script_result: VideoScriptResult = structured_llm.invoke(messages)
    return script_result


def script_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 9.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `video_script`.
    """
    selected_topic = state.get("selected_topic", {})
    if not selected_topic and state.get("content_plan"):
        selected_topic = state["content_plan"][0]

    brand_rules = state.get("brand_rules", [])
    script_result = run_script_agent(selected_topic, brand_rules)

    return {
        "video_script": script_result.model_dump(),
    }
