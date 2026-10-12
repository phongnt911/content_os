"""LangGraph Edge Routing & Conditional Edges.

Định nghĩa các hàm điều kiện rẽ nhánh và vòng lặp theo đặc tả:
- route_after_plan_approval: Rẽ nhánh sau Human Touchpoint 1
- route_after_text_review: Vòng lặp tự sửa bài (Self-Correction Loop: draft_score < 8 và text_revision_count < 2)
"""

from typing import Literal
from langgraph.graph import END
from core.state import ContentOSState


def route_after_plan_approval(state: ContentOSState) -> str:
    """Conditional Edge sau Human Touchpoint 1.
    
    Quy tắc:
    - Nếu plan_approved == True: Đi tiếp vào dây chuyền sản xuất ('generate_outline').
    - Nếu plan_approved == False: Kết thúc luồng (END).
    """
    if state.get("plan_approved", False):
        return "generate_outline"
    return END


def route_after_text_review(state: ContentOSState) -> str:
    """Conditional Edge cho vòng lặp tự sửa bài (Self-Correction Loop).
    
    Quy tắc:
    - Nếu draft_score < 8 VÀ text_revision_count < 2: Vòng lặp quay lại 'writer' kèm feedback.
    - Ngược lại (draft_score >= 8 HOẶC text_revision_count >= 2): Tiếp tục sang 'fact_check'.
    """
    draft_score = state.get("draft_score", 0)
    revision_count = state.get("text_revision_count", 0)

    # Loop Breaker Guard: Max 2 lần sửa
    if draft_score < 8 and revision_count < 2:
        return "writer"
    return "fact_check"
