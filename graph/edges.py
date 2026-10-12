"""LangGraph Edge Routing & Conditional Edges.

Định nghĩa các hàm điều kiện rẽ nhánh và vòng lặp theo đặc tả:
- route_after_plan_approval: Rẽ nhánh sau Human Touchpoint 1 (Fork song song 2 nhánh Text & Visual)
- route_after_text_review: Vòng lặp tự sửa bài viết (Loop breaker: max 2 lần)
- route_after_video_review: Vòng lặp render lại video nếu lỗi kỹ thuật (Loop breaker: max 1 lần)
"""

from typing import Union, List
from langgraph.graph import END
from core.state import ContentOSState


def route_after_plan_approval(state: ContentOSState) -> Union[List[str], str]:
    """Conditional Edge sau Human Touchpoint 1.
    
    Quy tắc:
    - Nếu plan_approved == True: Fork song song thành 2 nhánh:
      ['generate_outline', 'generate_video_script'].
    - Nếu plan_approved == False: Kết thúc luồng (END).
    """
    if state.get("plan_approved", False):
        return ["generate_outline", "generate_video_script"]
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


def route_after_video_review(state: ContentOSState) -> str:
    """Conditional Edge cho vòng kiểm định Video QA.
    
    Quy tắc:
    - Nếu video chưa đạt VÀ video_revision_count < 1: Quay lại 'video_editing' render lại.
    - Ngược lại: Sang 'generate_cover_image'.
    """
    is_approved = state.get("video_approved", False)
    revision_count = state.get("video_revision_count", 0)

    # Loop Breaker Guard: Max 1 lần render lại
    if not is_approved and revision_count < 1:
        return "video_editing"
    return "generate_cover_image"


def route_after_final_approval(state: ContentOSState) -> str:
    """Conditional Edge sau Human Touchpoint 3 (Duyệt trọn gói Final Package).
    
    Quy tắc:
    - Nếu final_package_approved == True: Tiến hành xuất bản ('publisher').
    - Nếu total_cycle_count > 4: Chuyển sang trạng thái dừng khẩn cấp HALTED (END).
    - Nếu cần sửa (total_cycle_count <= 4):
      + Nếu ghi chú sửa video/ảnh: Quay lại 'generate_video_script'.
      + Mặc định: Quay lại 'generate_outline' để sửa lại nội dung chữ.
    """
    if state.get("final_package_approved", False):
        return "publisher"

    cycle_count = state.get("total_cycle_count", 0)
    if cycle_count > 4:
        return END

    note = (state.get("user_revision_note") or "").lower()
    media_keywords = ["video", "clip", "dựng", "sub", "audio", "nhạc", "cover", "ảnh"]
    if any(kw in note for kw in media_keywords):
        return "generate_video_script"

    return "generate_outline"
