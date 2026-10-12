"""Agent 11: Video Review QA Agent (Visual Pipeline).

Nhiệm vụ:
- Kiểm định chất lượng kỹ thuật của video đã render:
  + Thời lượng bắt buộc < 60 giây (đạt chuẩn Short/Reels/TikTok).
  + Khớp phụ đề và âm thanh.
- Sử dụng structured output với schema `VideoReviewResult`.
- Tăng biến đếm `video_revision_count` (Loop Guard: tối đa 1 lần render lại nếu lỗi).
- Cập nhật trường `video_approved` và `video_revision_count` trong ContentOSState.
"""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, VideoReviewResult
from config import get_llm


VIDEO_REVIEW_SYSTEM_PROMPT = """Bạn là Agent 11 (Video Technical QA & Broadcast Inspector) thuộc POTA Content OS.
Nhiệm vụ của bạn:
1. Thẩm định thông số kỹ thuật của video:
   - Thời lượng thực tế (measured_duration): Bắt buộc < 60 giây.
   - Khớp phụ đề (subtitle_synced): True nếu phụ đề khớp lời thoại và không bị lỗi chính tả.
2. Đưa ra phán quyết:
   - video_approved: True nếu thời lượng < 60s và phụ đề đồng bộ tốt.
   - technical_feedback: Nhận xét kỹ thuật chi tiết.

Bắt buộc trả về đúng cấu trúc VideoReviewResult."""


def run_review_video_agent(
    video_url: str,
    duration: int,
    script: Dict[str, Any],
) -> VideoReviewResult:
    """Thực thi logic thẩm định video của Agent 11."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(VideoReviewResult)

    user_prompt = f"""Hãy thẩm định thông số video đã render:
- Đường dẫn video: {video_url}
- Thời lượng đo được: {duration} giây (Yêu cầu: < 60s)
- Kịch bản đối chiếu: {script.get('hook_opening', '')}

Xuất ra cấu trúc VideoReviewResult hoàn chỉnh."""

    messages = [
        SystemMessage(content=VIDEO_REVIEW_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    result: VideoReviewResult = structured_llm.invoke(messages)
    return result


def review_video_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 11.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `video_approved` và `video_revision_count`.
    """
    video_url = state.get("rendered_video_url") or "https://cdn.pota.media/sample.mp4"
    duration = state.get("video_duration", 45)
    script = state.get("video_script", {})
    current_revisions = state.get("video_revision_count", 0)

    result = run_review_video_agent(
        video_url=video_url,
        duration=duration,
        script=script,
    )

    new_revision_count = current_revisions
    if not result.video_approved:
        new_revision_count += 1

    return {
        "video_approved": result.video_approved,
        "video_revision_count": new_revision_count,
    }
