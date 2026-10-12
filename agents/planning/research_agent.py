"""Agent 1: Research Agent (Planning Layer).

Nhiệm vụ:
- Quét tin tức công nghệ, radar đối thủ và các cuộc thảo luận nổi bật.
- Lọc và xuất ra 5 chủ đề xu hướng (Trends Feed) có điểm liên quan cao nhất tới thương hiệu.
- Cập nhật trường `trends_feed` trong ContentOSState.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, ResearchReport, TrendTopic
from config import get_llm


RESEARCH_SYSTEM_PROMPT = """Bạn là Agent 1 (Research & Trend Scout) thuộc hệ thống LinTech Content OS.
Nhiệm vụ của bạn:
1. Phân tích các xu hướng công nghệ mới, AI Automation, kinh doanh số, và các góc nhìn thảo luận nóng nhất từ mạng xã hội/đối thủ.
2. Trích xuất chính xác 5 chủ đề xu hướng (Trends) tiềm năng nhất.
3. Mỗi chủ đề phải có:
   - id: Mã định danh dạng 'trend_01', 'trend_02'...
   - topic: Tên chủ đề súc tích, hấp dẫn.
   - source_radar: Nguồn phát hiện (ví dụ: TechCrunch, HackerNews, X/Twitter, Reddit, Đối thủ AI...).
   - trend_summary: Tóm tắt 2-3 câu vì sao chủ đề này đang được quan tâm và giá trị cốt lõi.
   - relevance_score: Điểm phù hợp với thương hiệu LinTech từ 0.0 đến 10.0.

Tuân thủ nghiêm ngặt Brand Rules của hệ thống nếu có."""


def run_research_agent(
    brand_rules: List[str],
    focus_topic: str = "",
) -> ResearchReport:
    """Thực thi logic cốt lõi của Agent 1 với structured output."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(ResearchReport)

    rules_context = "\n- ".join(brand_rules) if brand_rules else "Ưu tiên nội dung AI, Productivity, Solopreneur, No-code."
    topic_instruction = f"\nƯu tiên trọng tâm: Nghiên cứu sâu và phát triển 5 góc nhìn xoay quanh chủ đề: '{focus_topic}'." if focus_topic else ""

    user_prompt = f"""Hãy quét và tổng hợp 5 chủ đề xu hướng công nghệ nổi bật nhất cho tuần này.{topic_instruction}
Brand Rules hiện tại:
- {rules_context}

Yêu cầu xuất ra cấu trúc ResearchReport chứa đúng 5 TrendTopic."""

    messages = [
        SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    report: ResearchReport = structured_llm.invoke(messages)
    return report


def research_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 1.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `trends_feed`.
    """
    brand_rules = state.get("brand_rules", [])
    selected_topic = state.get("selected_topic", {})
    focus_topic = selected_topic.get("angle") or selected_topic.get("topic") or ""

    report = run_research_agent(brand_rules, focus_topic=focus_topic)

    trends_data = [trend.model_dump() for trend in report.trends]
    return {
        "trends_feed": trends_data
    }
