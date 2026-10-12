"""Agent 1: Research Agent (Planning Layer).

Nhiệm vụ:
- Quét tin tức, radar đối thủ và các cuộc thảo luận nổi bật theo từng ngành nghề.
- Lọc và xuất ra 5 chủ đề xu hướng (Trends Feed) có điểm liên quan cao nhất tới chủ đề người dùng và thương hiệu POTA.
- Cập nhật trường `trends_feed` trong ContentOSState.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, ResearchReport, TrendTopic
from config import get_llm


RESEARCH_SYSTEM_PROMPT = """Bạn là Agent 1 (Multi-Industry Research & Trend Scout) thuộc hệ thống POTA Content OS.
Nhiệm vụ của bạn:
1. Nghiên cứu, phân tích xu hướng thị trường, bối cảnh ngành nghề và các chủ đề thảo luận nóng nhất từ mạng xã hội/cộng đồng (Facebook, TikTok, Threads, YouTube, diễn đàn chuyên ngành).
2. Khi người dùng ĐÃ CUNG CẤP CHỦ ĐỀ TRỌNG TÂM:
   - Hãy bám sát 100% vào ngành nghề và chủ đề mà người dùng yêu cầu (bất kể là F&B, thời trang, bất động sản, giáo dục, sức khỏe, tài chính cá nhân, phong cách sống, kinh doanh hay công nghệ).
   - Tuyệt đối KHÔNG gượng ép lồng ghép công nghệ/AI nếu chủ đề của người dùng không liên quan đến công nghệ.
   - Bẻ nhỏ chủ đề thành 5 góc nhìn (angles) sắc bén, thực chiến và đa chiều:
     + Góc 1 (Pain-point): Đánh trúng nỗi đau, sai lầm phổ biến hoặc rào cản lớn nhất của đối tượng mục tiêu trong ngành.
     + Góc 2 (Case study/Thực chứng): Câu chuyện thực tế, bài học kinh nghiệm, ví dụ người thật việc thật hoặc sự đối chiếu trước - sau.
     + Góc 3 (Bí quyết/Quy trình): Hướng dẫn từng bước (Step-by-step), giải pháp cốt lõi, công thức hoặc cách làm thực thi hiệu quả.
     + Góc 4 (Tối ưu/Bài toán giá trị): Cách tiết kiệm chi phí, thời gian, gia tăng hiệu suất hoặc tối ưu hóa ROI cho độc giả.
     + Góc 5 (Xu hướng/Tầm nhìn): Dự báo xu hướng tương lai, lời khuyên hành động ngay để dẫn đầu trong lĩnh vực này.
   - Mỗi góc nhìn phải kèm số liệu ước tính hoặc dẫn chứng từ nguồn radar uy tín (báo cáo ngành, mạng xã hội, diễn đàn chuyên gia).
3. Khi người dùng CHƯA CUNG CẤP CHỦ ĐỀ (để trống):
   - Tự động quét và tổng hợp 5 chủ đề xu hướng kinh doanh, phát triển nội dung và giải pháp sáng tạo nổi bật nhất trong tuần có độ liên quan cao nhất tới thương hiệu POTA.
4. Trả về đúng 5 TrendTopic với định dạng ResearchReport chuẩn Pydantic."""


def run_research_agent(
    brand_rules: List[str],
    focus_topic: str = "",
) -> ResearchReport:
    """Thực thi logic cốt lõi của Agent 1 với structured output."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(ResearchReport)

    rules_context = "\n- ".join(brand_rules) if brand_rules else "Ưu tiên nội dung thực chiến, tạo giá trị thực, văn phong trực diện và cuốn hút."
    
    if focus_topic:
        user_prompt = f"""CHỦ ĐỀ YÊU CẦU TỪ NGƯỜI DÙNG: '{focus_topic}'
Hãy phân tích và phát triển 5 góc tiếp cận độc đáo, chuyên sâu xoay quanh ngành nghề và chủ đề trên kèm nguồn radar đối thủ và số liệu thực tế.
Lưu ý: Bám sát đúng lĩnh vực của chủ đề trên, không tự ý gán ghép sang công nghệ/AI nếu chủ đề không yêu cầu.

Brand Rules cần áp dụng:
- {rules_context}

Xuất ra cấu trúc ResearchReport gồm đúng 5 TrendTopic."""
    else:
        user_prompt = f"""Hãy quét và tổng hợp 5 chủ đề xu hướng kinh doanh và sáng tạo nội dung nổi bật nhất cho tuần này.

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
