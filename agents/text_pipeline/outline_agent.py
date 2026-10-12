"""Agent 3: Outline Agent (Text Pipeline).

Nhiệm vụ:
- Tiếp nhận `selected_topic` từ State (hoặc lấy từ bài đầu tiên của content_plan).
- Tạo dàn ý bài viết cấu trúc chuẩn mực:
  + Hook: Đúng 3 biến thể mở bài khác nhau (tò mò, tương phản, số liệu gây sốc).
  + Thân bài: Các luận điểm chính kèm dẫn chứng thực tế.
  + CTA: Lời kêu gọi hành động định hướng tương tác.
- Cập nhật trường `outline` trong ContentOSState.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, OutlineStructure
from config import get_llm


OUTLINE_SYSTEM_PROMPT = """Bạn là Agent 3 (Content Architect & Outline Specialist) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Phân tích chủ đề (selected_topic) và các quy chuẩn thương hiệu (brand_rules).
2. Xây dựng dàn ý chi tiết cho bài viết chuyên sâu:
   - topic_id: Mã bài viết tương ứng.
   - hook_variants: Đúng 3 biến thể hook mở bài khác nhau (Ví dụ: 1 hook giật gân/tò mò, 1 hook số liệu nghịch lý, 1 hook câu hỏi trúng pain-point).
   - body_points: Tối thiểu 3 luận điểm cốt lõi, mạch lạc, dễ hiểu.
   - call_to_action: Câu CTA rõ ràng, kích thích độc giả bình luận hoặc lưu bài.

Bắt buộc trả về đúng định dạng OutlineStructure."""


def run_outline_agent(
    selected_topic: Dict[str, Any],
    brand_rules: List[str],
) -> OutlineStructure:
    """Thực thi logic sinh dàn ý của Agent 3 với structured output."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(OutlineStructure)

    topic_id = selected_topic.get("id", "post_01")
    angle = selected_topic.get("angle", "Thực chiến công nghệ & AI")
    hook_concept = selected_topic.get("hook_concept", "Ý tưởng hook mở bài")
    core_message = selected_topic.get("core_message", "Thông điệp cốt lõi")
    target_channel = selected_topic.get("target_channel", "Facebook")

    rules_context = "\n- ".join(brand_rules) if brand_rules else "Tập trung giải quyết vấn đề thực tế, văn phong gãy gọn."

    user_prompt = f"""Hãy lập dàn ý bài viết chuyên sâu cho chủ đề sau:
- Mã bài: {topic_id}
- Kênh mục tiêu: {target_channel}
- Góc tiếp cận (Angle): {angle}
- Ý tưởng hook ban đầu: {hook_concept}
- Thông điệp cốt lõi: {core_message}

Brand Rules cần áp dụng:
- {rules_context}

Xuất ra cấu trúc OutlineStructure hoàn chỉnh."""

    messages = [
        SystemMessage(content=OUTLINE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    outline: OutlineStructure = structured_llm.invoke(messages)
    return outline


def outline_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 3.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `outline`.
    """
    selected_topic = state.get("selected_topic", {})
    if not selected_topic and state.get("content_plan"):
        selected_topic = state["content_plan"][0]

    brand_rules = state.get("brand_rules", [])
    outline_result = run_outline_agent(selected_topic, brand_rules)

    return {
        "outline": outline_result.model_dump(),
        "selected_topic": selected_topic,
    }
