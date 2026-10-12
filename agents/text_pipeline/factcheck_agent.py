"""Agent 6: Fact-check & Policy Agent (Text Pipeline).

Nhiệm vụ:
- Rà soát lỗi chính tả, ngữ pháp của bản thảo bài viết.
- Xác minh các con số, dữ liệu và luận cứ.
- Quét các từ khóa nhạy cảm có nguy cơ vi phạm tiêu chuẩn cộng đồng Meta / TikTok.
- Làm sạch và trả về `fact_checked_draft`.
"""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, FactCheckResult
from config import get_llm


FACTCHECK_SYSTEM_PROMPT = """Bạn là Agent 6 (Fact-Checker & Policy Compliance Officer) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Rà soát bài viết (raw_draft):
   - Quét lỗi chính tả, lỗi đánh máy, lỗi diễn đạt câu lủng củng.
   - Quét từ khóa vi phạm chính sách Meta/TikTok (ví dụ: cam kết 100%, từ ngữ bẫy spam, tuyên bố phóng đại sai sự thật...).
   - Kiểm tra tính hợp lý của các số liệu và dẫn chứng.
2. Trả về cấu trúc FactCheckResult:
   - has_policy_violation: True nếu có từ ngữ có nguy cơ bóp tương tác.
   - policy_issues: Danh sách các vấn đề chính sách (nếu có).
   - spelling_errors: Danh sách các lỗi chính tả đã phát hiện và sửa.
   - verified_claims: Các tuyên bố đã được xác thực tính hợp lý.
   - cleaned_draft: Bản thảo hoàn chỉnh đã được sửa hết lỗi chính tả và điều chỉnh từ ngữ an toàn tuyệt đối.

Bắt buộc trả về đúng cấu trúc FactCheckResult."""


def run_factcheck_agent(raw_draft: str) -> FactCheckResult:
    """Thực thi logic kiểm chứng và rà soát lỗi của Agent 6."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(FactCheckResult)

    user_prompt = f"""Hãy rà soát kỹ lưỡng lỗi chính tả và chính sách cho bài viết sau:

=== BẢN THẢO BÀI VIẾT ===
{raw_draft}

Xuất ra cấu trúc FactCheckResult hoàn chỉnh."""

    messages = [
        SystemMessage(content=FACTCHECK_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    result: FactCheckResult = structured_llm.invoke(messages)
    return result


def factcheck_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 6.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `fact_checked_draft`.
    """
    raw_draft = state.get("raw_draft", "")
    result = run_factcheck_agent(raw_draft)

    return {
        "fact_checked_draft": result.cleaned_draft or raw_draft
    }
