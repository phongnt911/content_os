"""Agent 7: Repurpose Agent (Threads Pipeline).

Nhiệm vụ:
- Tiếp nhận `fact_checked_draft` (hoặc `raw_draft`).
- Chuyển thể nội dung thành chuỗi 3 đến 5 bài đăng ngắn (Thread Series) tối ưu cho nền tảng Threads/X.
- Cập nhật trường `threads_posts` trong ContentOSState.
"""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, RepurposeThreadsResult
from config import get_llm


REPURPOSE_SYSTEM_PROMPT = """Bạn là Agent 7 (Social Repurposing & Threads Master) thuộc POTA Content OS.
Nhiệm vụ của bạn:
1. Tiếp nhận bài viết dài đã được làm sạch lỗi (fact_checked_draft).
2. Tách nhỏ và biên tập lại thành chuỗi từ 3 đến 5 post ngắn trên Threads:
   - Post 1 (Hook): Giật hook mạnh, ngắn gọn, gây tò mò cực cao.
   - Các Post tiếp theo (Body): Mỗi post nêu 1 ý súc tích, dễ chia sẻ, nhịp đọc nhanh.
   - Post cuối cùng (CTA): Câu chốt kêu gọi bình luận quan điểm hoặc follow.
3. Độ dài mỗi post nên từ 100 - 250 ký tự, định dạng đánh số rõ ràng (1/, 2/, 3/...).

Bắt buộc trả về đúng cấu trúc RepurposeThreadsResult."""


def run_repurpose_agent(source_draft: str) -> RepurposeThreadsResult:
    """Thực thi logic chuyển đổi sang chuỗi Threads của Agent 7."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(RepurposeThreadsResult)

    user_prompt = f"""Hãy chuyển đổi bài viết sau thành một chuỗi 3 đến 5 post Threads hấp dẫn:

=== BÀI VIẾT NGUỒN ===
{source_draft}

Xuất ra cấu trúc RepurposeThreadsResult hoàn chỉnh."""

    messages = [
        SystemMessage(content=REPURPOSE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    result: RepurposeThreadsResult = structured_llm.invoke(messages)
    return result


def repurpose_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 7.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `threads_posts`.
    """
    draft = state.get("fact_checked_draft") or state.get("raw_draft", "")
    if not draft:
        draft = "Nội dung bài viết ngắn gọn chuẩn bị cho chuỗi bài Threads của POTA."

    result = run_repurpose_agent(draft)

    return {
        "threads_posts": result.threads_posts,
    }
