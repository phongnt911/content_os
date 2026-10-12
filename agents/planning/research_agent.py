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
1. Nghiên cứu, phân tích xu hướng thị trường, bối cảnh ngành nghề và các chủ đề thảo luận nóng nhất từ mạng xã hội/cộng đồng (Facebook, TikTok, Threads, YouTube, báo chí, diễn đàn).
2. Khi người dùng ĐÃ CUNG CẤP CHỦ ĐỀ TRỌNG TÂM:
   - Hãy bám sát 100% vào ngữ cảnh và bản chất của chủ đề mà người dùng yêu cầu:
     + Nếu là NÔNG SẢN / ẨM THỰC / ĐẶC SẢN VÙNG MIỀN (Ví dụ: "xoài cam lâm", "cà phê Cầu Đất", "sầu riêng", "yến sào"):
       * Tuyệt đối KHÔNG dùng ngôn ngữ sáo rỗng kiểu startup/kinh doanh (cấm dùng "thực chiến", "đột phá 30 ngày", "tối ưu ROI", "làm việc chăm chỉ").
       * Bẻ nhỏ thành 5 góc nhìn gần gũi, đời sống và giàu giá trị thực tế:
         - Góc 1 (Nguồn gốc & Độc bản): Thổ nhưỡng, giống cây, điều làm nên hương vị khác biệt của vùng đất.
         - Góc 2 (Kinh nghiệm tiêu dùng): Mẹo nhận biết hàng loại 1 chuẩn chín cây, phân biệt với hàng ngâm thuốc hoặc hàng dạt.
         - Góc 3 (Ẩm thực & Thưởng thức): Cách ăn đúng điệu, các món ngon chế biến từ đặc sản, công thức độc đáo.
         - Góc 4 (Sức khỏe & Dinh dưỡng): Giá trị dinh dưỡng, công dụng cho sức khỏe gia đình, lưu ý khi ăn.
         - Góc 5 (Thị trường & Mùa vụ): Mùa thu hoạch rộ, giá cả tại vườn, kết nối tiêu thụ nông sản Việt uy tín.
     + Nếu là KINH DOANH / DỊCH VỤ / TÀI CHÍNH / BÁN HÀNG:
       * Tiếp cận theo bài toán thị trường, quản lý chi phí, kinh nghiệm phục vụ khách hàng và giải pháp sinh lời bền vững.
     + Nếu là CÔNG NGHỆ / PHẦN MỀM:
       * Mới phân tích kiến trúc kỹ thuật, giải pháp tự động hóa và công cụ năng suất.
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

    rules_context = "\n- ".join(brand_rules) if brand_rules else "Ưu tiên nội dung tự nhiên, tạo giá trị thực cho người đọc, văn phong thuần Việt, đúng ngữ cảnh đề tài."
    
    if focus_topic:
        user_prompt = f"""CHỦ ĐỀ YÊU CẦU TỪ NGƯỜI DÙNG: '{focus_topic}'
Hãy phân tích và phát triển 5 góc tiếp cận độc đáo, chuyên sâu xoay quanh bản chất thật của chủ đề trên.
LƯU Ý QUAN TRỌNG:
- Nhận diện đúng ngành nghề của chủ đề (nông sản, ẩm thực, thời trang, kỹ thuật hay kinh doanh).
- Dùng từ ngữ tự nhiên, phù hợp với đời sống và tâm lý độc giả của ngành đó.
- Tuyệt đối không dùng văn mẫu startup sáo rỗng nếu chủ đề là nông sản hay ẩm thực.

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
