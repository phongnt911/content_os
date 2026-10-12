"""Agent 12: Cover & Thumbnail Agent (Visual Pipeline).

Nhiệm vụ:
- Tiếp nhận chủ đề bài viết và kịch bản video.
- Tạo prompt sinh ảnh thumbnail chất lượng cao với 2 tỉ lệ:
  + Tỉ lệ 3:4 cho Facebook và Instagram.
  + Tỉ lệ 9:16 cho TikTok và YouTube Shorts / Reels.
- Thiết kế tiêu đề đè lên ảnh (overlay_headline) và quy định vùng an toàn (safe zone).
- Cập nhật trường `cover_image_url` trong ContentOSState.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, CoverPromptResult
from config import get_llm


COVER_SYSTEM_PROMPT = """Bạn là Agent 12 (Visual Branding & Cover Thumbnail Artist) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Phân tích kịch bản video và chủ đề nội dung.
2. Thiết kế định hướng ảnh bìa thumbnail thu hút lượt click (High CTR):
   - prompt_3_4: Prompt chi tiết bằng tiếng Anh sinh ảnh bìa tỉ lệ 3:4 cho Facebook/Instagram Feed (Midjourney / Flux format).
   - prompt_9_16: Prompt chi tiết bằng tiếng Anh sinh ảnh bìa tỉ lệ 9:16 cho TikTok / Shorts / Reels.
   - overlay_headline: Dòng chữ giật tít ngắn gọn (dưới 6 từ, in hoa, tạo sự tương phản mạnh) đè lên ảnh.
   - safe_zone_notes: Hướng dẫn đặt chữ tránh các nút Like, Comment, Caption của ứng dụng.

Bắt buộc trả về đúng cấu trúc CoverPromptResult."""


def run_cover_agent(
    selected_topic: Dict[str, Any],
    video_script: Dict[str, Any],
    brand_rules: List[str],
) -> CoverPromptResult:
    """Thực thi logic thiết kế prompt thumbnail của Agent 12."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(CoverPromptResult)

    topic_title = selected_topic.get("angle", "AI Automation Workflow")
    hook = video_script.get("hook_opening", "Tự động hóa video trong 30 giây")
    rules_context = "\n- ".join(brand_rules) if brand_rules else "Gam màu công nghệ hiện đại, độ tương phản cao."

    user_prompt = f"""Hãy thiết kế bộ prompt và layout ảnh bìa thumbnail cho video sau:
- Chủ đề: {topic_title}
- Hook mở đầu: {hook}

Brand Rules:
- {rules_context}

Xuất ra cấu trúc CoverPromptResult hoàn chỉnh."""

    messages = [
        SystemMessage(content=COVER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    result: CoverPromptResult = structured_llm.invoke(messages)
    return result


def cover_agent_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 12.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `cover_image_url`.
    """
    selected_topic = state.get("selected_topic", {})
    video_script = state.get("video_script", {})
    brand_rules = state.get("brand_rules", [])

    cover_result = run_cover_agent(selected_topic, video_script, brand_rules)

    # Sinh link thumbnail mẫu theo chuẩn CDN
    topic_id = selected_topic.get("id", "post_01")
    generated_cover_url = f"https://cdn.lintech.media/thumbnails/{topic_id}_cover_3x4.jpg"

    return {
        "cover_image_url": generated_cover_url
    }
