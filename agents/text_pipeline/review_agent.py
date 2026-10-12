"""Agent 5: Review Agent (QA & Self-Correction Evaluator).

Nhiệm vụ:
- Kiểm tra bài viết `raw_draft` từ Agent 4 theo tiêu chuẩn chất lượng và Brand Rules.
- Chấm điểm trên thang 0 - 10 và nhận xét chi tiết.
- Bắt buộc sử dụng `.with_structured_output(DraftReviewResult)` theo Rule 4.
- Cập nhật các trường `draft_score`, `draft_feedback`, và tăng `text_revision_count`.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, DraftReviewResult
from config import get_llm


REVIEW_SYSTEM_PROMPT = """Bạn là Agent 5 (Chief Quality Officer & Editor-in-Chief) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Đọc kỹ bản thảo bài viết (raw_draft), đối chiếu với dàn ý (outline) và các quy chuẩn thương hiệu (brand_rules).
2. Chấm điểm bài viết trên thang điểm từ 0 đến 10 (draft_score):
   - >= 8 điểm: Bài viết đạt chuẩn xuất sắc (hook cuốn hút, luận điểm chặt chẽ, CTA tự nhiên, đúng Brand Voice).
   - < 8 điểm: Bài viết chưa đạt chuẩn (còn dài dòng, hook yếu, thiếu ví dụ thực tế hoặc vi phạm brand rules).
3. Cung cấp nhận xét chi tiết (draft_feedback):
   - strengths: Những điểm làm tốt.
   - improvements: Những điểm bắt buộc phải viết lại hoặc cải thiện nếu điểm < 8.
   - approved: True nếu draft_score >= 8, ngược lại False.

Bắt buộc trả về đúng cấu trúc DraftReviewResult."""


def run_review_agent(
    raw_draft: str,
    outline: Dict[str, Any],
    brand_rules: List[str],
) -> DraftReviewResult:
    """Thực thi logic chấm điểm của Agent 5 với structured output bắt buộc."""
    llm = get_llm(model_type="core")
    structured_llm = llm.with_structured_output(DraftReviewResult)

    rules_str = "\n- ".join(brand_rules) if brand_rules else "Tiêu chuẩn: Hook mạnh, thân bài có số liệu/ví dụ, CTA rõ."
    topic_id = outline.get("topic_id", "N/A")

    user_prompt = f"""Hãy đánh giá và chấm điểm bản thảo bài viết sau đây:
Mã chủ đề: {topic_id}

=== BẢN THẢO (RAW DRAFT) ===
{raw_draft}

=== BRAND RULES CẦN ĐỐI CHIẾU ===
- {rules_str}

Hãy thẩm định kỹ lưỡng và xuất ra cấu trúc DraftReviewResult."""

    messages = [
        SystemMessage(content=REVIEW_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    result: DraftReviewResult = structured_llm.invoke(messages)
    return result


def review_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 5.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `draft_score`, `draft_feedback`,
    và tăng biến đếm `text_revision_count`.
    """
    raw_draft = state.get("raw_draft", "")
    outline = state.get("outline", {})
    brand_rules = state.get("brand_rules", [])
    current_revisions = state.get("text_revision_count", 0)

    review_result = run_review_agent(raw_draft, outline, brand_rules)

    return {
        "draft_score": review_result.draft_score,
        "draft_feedback": review_result.draft_feedback,
        "text_revision_count": current_revisions + 1,
    }
