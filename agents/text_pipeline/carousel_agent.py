"""Agent 8: Carousel Agent (Text Pipeline).

Nhiệm vụ:
- Tiếp nhận bài viết đã hoàn thiện.
- Cắt lát nội dung thành bộ kịch bản slide Carousel đa trang (5 đến 7 trang) cho Facebook/Instagram/LinkedIn.
- Mỗi slide có: headline, body_content, visual_layout_tip.
- Cập nhật trường `carousel_slides` trong ContentOSState.
"""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, CarouselResult
from config import get_llm


CAROUSEL_SYSTEM_PROMPT = """Bạn là Agent 8 (Visual Storytelling & Carousel Specialist) thuộc POTA Content OS.
Nhiệm vụ của bạn:
1. Tiếp nhận nội dung bài viết hoàn chỉnh (fact_checked_draft).
2. Tái cấu trúc thành kịch bản slide Carousel ảnh từ 5 đến 7 trang:
   - Slide 1: Trang bìa (Cover) có tiêu đề giật tò mò cực lớn, ít chữ.
   - Các slide giữa (2 - 4/6): Mỗi slide trình bày 1 ý quan trọng, chữ ngắn gọn (dưới 40 từ), có gợi ý bố cục đồ họa (visual_layout_tip).
   - Slide cuối cùng: Trang kết luận và CTA (kêu gọi lưu bài, share hoặc comment).
3. Đảm bảo trải nghiệm lướt mượt mà, giữ chân độc giả từ slide đầu tới slide cuối.

Bắt buộc trả về đúng cấu trúc CarouselResult."""


def run_carousel_agent(source_draft: str) -> CarouselResult:
    """Thực thi logic chia slide Carousel của Agent 8."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(CarouselResult)

    user_prompt = f"""Hãy chuyển đổi bài viết sau thành bộ kịch bản slide Carousel 5-7 trang hấp dẫn:

=== BÀI VIẾT NGUỒN ===
{source_draft}

Xuất ra cấu trúc CarouselResult hoàn chỉnh."""

    messages = [
        SystemMessage(content=CAROUSEL_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    result: CarouselResult = structured_llm.invoke(messages)
    return result


def carousel_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 8.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `carousel_slides`.
    """
    draft = state.get("fact_checked_draft") or state.get("raw_draft", "")
    if not draft:
        draft = "Ý tưởng bài viết phân tích giá trị thực tiễn cho cộng đồng POTA."

    result = run_carousel_agent(draft)

    slides_data = [s.model_dump() for s in result.slides]
    return {
        "carousel_slides": slides_data,
    }
