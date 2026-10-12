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


RESEARCH_SYSTEM_PROMPT = """Bạn là Agent 1 (Research & Trend Scout) thuộc hệ thống PoTa Content OS.
Nhiệm vụ của bạn:
1. Phân tích các xu hướng công nghệ, AI Automation, kinh doanh số, và các góc nhìn thảo luận nóng nhất từ mạng xã hội/đối thủ.
2. Nếu người dùng ĐÃ CUNG CẤP CHỦ ĐỀ TRỌNG TÂM:
   - Hãy bẻ nhỏ chủ đề đó thành 5 góc nhìn (angles) chuyên sâu và đa chiều:
     + Góc 1: Đánh trúng pain-point hoặc sai lầm 90% người mắc phải.
     + Góc 2: Case study thực chiến so sánh hiệu quả trước và sau khi ứng dụng.
     + Góc 3: Phân tích kỹ thuật / kiến trúc hệ thống chuyên sâu.
     + Góc 4: Bài toán chi phí, ROI và tối ưu nguồn lực.
     + Góc 5: Xu hướng tương lai và lời khuyên hành động ngay.
   - Mỗi góc nhìn phải kèm số liệu hoặc dẫn chứng radar uy tín (TechCrunch, X/Twitter, Reddit, HackerNews).
3. Nếu người dùng CHƯA CUNG CẤP CHỦ ĐỀ:
   - Tự động quét và trích xuất 5 xu hướng công nghệ nổi bật nhất trong tuần có độ liên quan cao nhất tới thương hiệu.
4. Trả về đúng 5 TrendTopic với định dạng ResearchReport chuẩn Pydantic."""


def run_research_agent(
    brand_rules: List[str],
    focus_topic: str = "",
) -> ResearchReport:
    """Thực thi logic cốt lõi của Agent 1 với structured output."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(ResearchReport)

    rules_context = "\n- ".join(brand_rules) if brand_rules else "Ưu tiên nội dung AI, Productivity, Solopreneur, No-code."
    
    if focus_topic:
        user_prompt = f"""CHỦ ĐỀ YÊU CẦU TỪ NGƯỜI DÙNG: '{focus_topic}'
Hãy phân tích và phát triển 5 góc tiếp cận độc đáo, chuyên sâu xoay quanh chủ đề trên kèm nguồn radar đối thủ và số liệu thực tế.

Brand Rules cần áp dụng:
- {rules_context}

Xuất ra cấu trúc ResearchReport gồm đúng 5 TrendTopic."""
    else:
        user_prompt = f"""Hãy quét và tổng hợp 5 chủ đề xu hướng công nghệ nổi bật nhất cho tuần này.

Brand Rules hiện tại:
- {rules_context}

Xuất ra cấu trúc ResearchReport chứa đúng 5 TrendTopic."""

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
