"""Agent 4: Writer Agent (Text Pipeline).

Nhiệm vụ:
- Tiếp nhận `outline` từ Agent 3 và `brand_rules`.
- Chấp bút bài viết hoàn chỉnh (bài dài Facebook) theo đúng phong cách Brand Voice.
- Nếu có `draft_feedback` từ Agent 5 (trong vòng lặp tự sửa bài), viết lại hoặc tinh chỉnh bài viết khắc phục triệt để các điểm yếu được chỉ ra.
- Cập nhật trường `raw_draft` trong ContentOSState.
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState
from config import get_llm


WRITER_SYSTEM_PROMPT = """Bạn là Agent 4 (Master Copywriter & Brand Voice Specialist) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Viết một bài viết hoàn chỉnh chuẩn phong cách Facebook / Blog chuyên sâu dựa trên Dàn ý (Outline) được cung cấp.
2. Cấu trúc bài viết:
   - Hook mở đầu: Chọn 1 hook cuốn hút nhất từ 3 biến thể trong dàn ý.
   - Thân bài: Đi sâu vào từng luận điểm, dùng ví dụ cụ thể, gạch đầu dòng rõ ràng, ngắt dòng dễ đọc trên thiết bị di động.
   - Kêu gọi hành động (CTA): Khớp với dàn ý, tạo sự tương tác tự nhiên.
3. Brand Voice:
   - Chuyên nghiệp, thực chiến, không màu mè sáo rỗng.
   - Tối ưu nhịp điệu đọc (pacing), tránh những câu quá dài.

Nếu có NHẬN XÉT SỬA BÀI (Feedback) từ reviewer, hãy đọc kỹ và sửa chữa đúng các điểm được yêu cầu."""


def run_writer_agent(
    outline: Dict[str, Any],
    brand_rules: List[str],
    draft_feedback: Optional[str] = None,
    previous_draft: Optional[str] = None,
) -> str:
    """Thực thi logic viết bài của Agent 4."""
    llm = get_llm(model_type="core")

    topic_id = outline.get("topic_id", "N/A")
    hooks = outline.get("hook_variants", [])
    hooks_str = "\n".join([f"  + {h}" for h in hooks]) if hooks else "Tự tạo hook cuốn hút."
    body_points = outline.get("body_points", [])
    body_str = "\n".join([f"  + {b}" for b in body_points]) if body_points else "Phân tích vấn đề và giải pháp thực tế."
    cta = outline.get("call_to_action", "Thảo luận bên dưới.")

    rules_str = "\n- ".join(brand_rules) if brand_rules else "Tập trung giải quyết vấn đề thực tế."

    feedback_section = ""
    if draft_feedback:
        feedback_section = f"""
=== LƯU Ý VIẾT LẠI TỪ BẢN TRƯỚC (FEEDBACK) ===
{draft_feedback}

Bản thảo trước đó để tham khảo và nâng cấp:
{previous_draft or 'Chưa có bản thảo trước.'}
"""

    user_prompt = f"""Hãy viết bài viết hoàn chỉnh dựa trên dàn ý sau:
Mã chủ đề: {topic_id}

=== DÀN Ý BÀI VIẾT ===
- Các biến thể Hook gợi ý:
{hooks_str}
- Các luận điểm thân bài:
{body_str}
- Kêu gọi hành động (CTA): {cta}

=== BRAND RULES ===
- {rules_str}
{feedback_section}

Hãy viết bài viết hoàn chỉnh trực tiếp (bằng tiếng Việt):"""

    messages = [
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    content = getattr(response, "content", str(response)).strip()
    return content


def writer_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 4.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `raw_draft`.
    """
    outline = state.get("outline", {})
    brand_rules = state.get("brand_rules", [])
    draft_feedback = state.get("draft_feedback")
    previous_draft = state.get("raw_draft")

    draft_text = run_writer_agent(
        outline=outline,
        brand_rules=brand_rules,
        draft_feedback=draft_feedback,
        previous_draft=previous_draft,
    )

    return {
        "raw_draft": draft_text
    }
