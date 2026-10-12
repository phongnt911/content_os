"""Agent 16: Analytics & Learner Agent (Operations Layer).

Nhiệm vụ:
- Tổng hợp chỉ số tương tác tuần của các ấn phẩm đã xuất bản (Facebook, TikTok, Threads, Shorts).
- Phân tích góc tiếp cận (Angle) thành công nhất và lý do độc giả tương tác cao.
- Trích xuất các bài học đắt giá thành các quy tắc mới (Learned Rules).
- Tự động bổ sung các quy tắc này vào `brand_rules` qua reducer `operator.add` trong ContentOSState,
  giúp Brand Brain ngày càng thông minh hơn qua từng chu kỳ sản xuất nội dung.
- Cập nhật trường `weekly_metrics` trong ContentOSState.
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, AnalyticsReportResult
from config import get_llm


ANALYTICS_SYSTEM_PROMPT = """Bạn là Agent 16 (Continuous Learning & Performance Analyst) thuộc POTA Content OS.
Nhiệm vụ của bạn:
1. Đánh giá số liệu tương tác tuần của bài viết và video đã phát hành.
2. Nhận diện góc tiếp cận chiến thắng (Winning Angles) tạo ra lượng reach hoặc conversion cao nhất.
3. Đúc rút 1-2 bài học thực chiến súc tích làm quy tắc mới (learned_rules) để bổ sung vào Brand Guidelines cho các tuần tiếp theo.

Bắt buộc trả về đúng định dạng AnalyticsReportResult."""


def run_analytics_agent(
    state: ContentOSState,
    simulated_metrics: Optional[Dict[str, Any]] = None,
) -> AnalyticsReportResult:
    """Thực thi logic phân tích và học máy của Agent 16 với structured output."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(AnalyticsReportResult)

    selected_topic = state.get("selected_topic", {})
    angle = selected_topic.get("angle", "Chiến lược nội dung thực chiến")
    published_links = state.get("published_links", {})
    current_brand_rules = state.get("brand_rules", [])

    metrics = simulated_metrics or {
        "facebook_reach": 12500,
        "facebook_shares": 142,
        "tiktok_views": 85000,
        "tiktok_retention_rate": "42%",
        "threads_impressions": 18200,
        "shorts_views": 32000,
        "cta_comments_count": 210,
        "lead_conversions": 94,
    }

    user_prompt = f"""Hãy phân tích hiệu quả tuần cho nội dung sau:
- Góc bài viết đã chạy: {angle}
- Các liên kết đã xuất bản: {published_links}
- Số liệu tương tác tuần thực tế:
{metrics}

Brand Rules hiện có:
- {"\n- ".join(current_brand_rules[:3])}

Xuất ra báo cáo AnalyticsReportResult kèm các quy tắc rút ra mới (learned_rules)."""

    messages = [
        SystemMessage(content=ANALYTICS_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    report: AnalyticsReportResult = structured_llm.invoke(messages)
    return report


def analytics_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 16.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `weekly_metrics`
    và `brand_rules` (được cộng dồn vào danh sách nhờ Annotated[List[str], operator.add]).
    """
    report = run_analytics_agent(state)

    return {
        "weekly_metrics": {
            "metrics_summary": report.metrics_summary,
            "winning_angles": report.winning_angles,
        },
        "brand_rules": report.learned_rules,
    }
