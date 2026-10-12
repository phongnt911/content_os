"""Agent 2: Planner Agent (Planning Layer).

Nhiệm vụ:
- Tiếp nhận 5 chủ đề xu hướng từ `trends_feed` của Agent 1.
- Kết hợp với `brand_rules` và `week_id`.
- Sử dụng .with_structured_output(WeeklyContentPlan) để sinh ma trận kế hoạch 5-7 bài/tuần.
- Mỗi bài viết ở dạng brief hoàn chỉnh: {id, angle, hook_concept, target_channel, target_audience, core_message}.
- Cập nhật trường `content_plan` trong ContentOSState.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, WeeklyContentPlan, ContentPlanItem
from config import get_llm, DEFAULT_WEEK_ID


PLANNER_SYSTEM_PROMPT = """Bạn là Agent 2 (Content Matrix & Chief Content Strategist) thuộc hệ thống POTA Content OS.
Nhiệm vụ của bạn:
1. Đọc danh sách 5 chủ đề xu hướng (trends_feed) và các quy chuẩn thương hiệu (brand_rules).
2. Xây dựng ma trận kế hoạch nội dung hàng tuần gồm từ 5 đến 7 bài viết đa kênh, bám sát ngành nghề và đối tượng độc giả mục tiêu của chủ đề.
3. Mỗi bài viết bắt buộc phải có cấu trúc brief rõ ràng:
   - id: 'post_01', 'post_02', ...
   - angle: Góc tiếp cận độc đáo, đúng ngữ cảnh thực tế của đề tài.
   - hook_concept: Ý tưởng hook mở bài có tính tò mò, bất ngờ hoặc kích thích độc giả phù hợp với đề tài.
   - target_channel: Kênh phân phối chính (Facebook, TikTok, Threads, Shorts, YouTube...).
   - target_audience: Chân dung đối tượng độc giả mục tiêu phù hợp với ngành.
   - core_message: Giá trị thực tiễn hoặc cảm xúc rút ra được sau bài viết.
4. NGUYÊN TẮC QUAN TRỌNG VỀ GIỌNG ĐIỆU & NGỮ CẢNH:
   - Nếu chủ đề về NÔNG SẢN / ẨM THỰC / ĐẶC SẢN (ví dụ: xoài Cam Lâm, sầu riêng, cà phê, bún chả...):
     + Hook và Góc bài phải tự nhiên, khơi gợi cảm giác ngon miệng, tò mò về nguồn gốc, mẹo chọn quả ngon, bảo quản, công thức chế biến hoặc câu chuyện người nông dân.
     + TUYỆT ĐỐI KHÔNG dùng các hook kinh doanh sáo rỗng (cấm dùng: "tại sao người giỏi nhất không chăm chỉ nhất", "đột phá 30 ngày", "đòn bẩy 80/20", "tối ưu ROI").
   - Nếu chủ đề về KINH DOANH / NGHỀ NGHIỆP: Mới dùng các hook về tối ưu thời gian, chi phí và hiệu suất.

Bắt buộc trả về đúng định dạng WeeklyContentPlan."""


def run_planner_agent(
    trends_feed: List[Dict[str, Any]],
    brand_rules: List[str],
    week_id: str = DEFAULT_WEEK_ID,
    focus_topic: str = "",
) -> WeeklyContentPlan:
    """Thực thi logic cốt lõi của Agent 2 với structured output bắt buộc theo Rule 4."""
    llm = get_llm(model_type="core")
    structured_llm = llm.with_structured_output(WeeklyContentPlan)

    trends_context = "\n".join([
        f"- [{t.get('id', 'N/A')}] {t.get('topic', 'Chủ đề')} (Nguồn: {t.get('source_radar', 'Radar')}): {t.get('trend_summary', '')}"
        for t in trends_feed
    ]) if trends_feed else "Chưa có trends_feed. Tự đề xuất các góc bài mang lại giá trị cao nhất cho độc giả."

    rules_context = "\n".join([f"- {r}" for r in brand_rules]) if brand_rules else "Tập trung giá trị thực tế, tự nhiên, đúng ngữ cảnh đề tài."
    focus_instruction = f"\n=== CHỦ ĐỀ TRỌNG TÂM DO USER YÊU CẦU ===\nToàn bộ hoặc ít nhất 2-3 bài viết trong ma trận bắt buộc phải khai thác chuyên sâu về: '{focus_topic}'\n" if focus_topic else ""

    user_prompt = f"""Hãy lập ma trận kế hoạch nội dung tuần {week_id} gồm từ 5 đến 7 bài viết.
{focus_instruction}
=== TRENDS RADAR ĐƯỢC CHỌN ===
{trends_context}

=== BRAND RULES CẦN TUÂN THỦ ===
{rules_context}

LƯU Ý: Đặt Hook và Angle phải hoàn toàn phù hợp với bản chất chủ đề '{focus_topic or 'Đa ngành'}', văn phong thuần Việt, tự nhiên và gần gũi.

Hãy xuất ra cấu trúc WeeklyContentPlan hoàn chỉnh."""

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    plan: WeeklyContentPlan = structured_llm.invoke(messages)
    return plan


def planner_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 2.
    
    Nhận `state: ContentOSState`, trả về dictionary cập nhật `content_plan`.
    """
    trends_feed = state.get("trends_feed", [])
    brand_rules = state.get("brand_rules", [])
    week_id = state.get("week_id", DEFAULT_WEEK_ID)
    selected_topic = state.get("selected_topic", {})
    focus_topic = selected_topic.get("angle") or selected_topic.get("topic") or ""

    plan = run_planner_agent(trends_feed, brand_rules, week_id, focus_topic=focus_topic)

    plan_items_data = [item.model_dump() for item in plan.items]
    return {
        "content_plan": plan_items_data
    }
