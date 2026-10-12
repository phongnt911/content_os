"""Agent 13: Image Review QA Agent (Visual Pipeline).

Nhiệm vụ:
- Kiểm tra thiết kế ảnh thumbnail từ Agent 12:
  + Đúng màu sắc nhận diện thương hiệu và logo (brand guidelines).
  + Vùng an toàn (safe zone) không bị che lấp bởi giao diện mạng xã hội.
  + Font chữ rõ ràng, dễ đọc trên màn hình điện thoại.
- Tăng biến đếm `image_revision_count` (Guard: Max 2).
- Cập nhật trường `image_approved` và `image_revision_count` trong ContentOSState.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, ImageReviewResult
from config import get_llm


IMAGE_REVIEW_SYSTEM_PROMPT = """Bạn là Agent 13 (Brand Identity & Thumbnail Art Director) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Thẩm định thiết kế ảnh bìa thumbnail:
   - brand_guidelines_met: True nếu màu sắc, phong cách hình ảnh phù hợp với thương hiệu LinTech.
   - safe_zone_valid: True nếu tiêu đề nằm trong vùng an toàn, không bị che bởi avatar, like/share icons.
2. Đưa ra quyết định:
   - image_approved: True nếu cả 2 tiêu chí trên đều đạt chuẩn.
   - feedback: Góp ý cải thiện màu sắc hoặc bố cục chữ.

Bắt buộc trả về đúng cấu trúc ImageReviewResult."""


def run_review_image_agent(
    cover_image_url: str,
    brand_rules: List[str],
) -> ImageReviewResult:
    """Thực thi logic duyệt ảnh thumbnail của Agent 13."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(ImageReviewResult)

    rules_context = "\n- ".join(brand_rules) if brand_rules else "Gam màu công nghệ hiện đại, độ tương phản cao, chữ dễ đọc."

    user_prompt = f"""Hãy thẩm định ảnh bìa thumbnail sau:
- Đường dẫn ảnh: {cover_image_url}

Brand Rules:
- {rules_context}

Xuất ra cấu trúc ImageReviewResult hoàn chỉnh."""

    messages = [
        SystemMessage(content=IMAGE_REVIEW_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    result: ImageReviewResult = structured_llm.invoke(messages)
    return result


def review_image_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 13.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `image_approved` và tăng `image_revision_count`.
    """
    cover_image_url = state.get("cover_image_url") or "https://cdn.lintech.media/sample_thumb.jpg"
    brand_rules = state.get("brand_rules", [])
    current_revisions = state.get("image_revision_count", 0)

    review_result = run_review_image_agent(cover_image_url, brand_rules)

    return {
        "image_approved": review_result.image_approved,
        "image_revision_count": current_revisions + 1,
    }
