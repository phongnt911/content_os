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


PLANNER_SYSTEM_PROMPT = """Bạn là Agent 2 (Content Matrix & Chief Content Strategist) thuộc hệ thống LinTech Content OS.
Nhiệm vụ của bạn:
1. Đọc danh sách 5 chủ đề xu hướng (trends_feed) và các quy chuẩn thương hiệu (brand_rules).
2. Xây dựng ma trận kế hoạch nội dung hàng tuần gồm từ 5 đến 7 bài viết đa kênh.
3. Mỗi bài viết bắt buộc phải có cấu trúc brief rõ ràng:
   - id: 'post_01', 'post_02', ...
   - angle: Góc tiếp cận độc đáo, đánh trúng pain-point hoặc kỳ vọng của độc giả.
   - hook_concept: Ý tưởng hook mở bài có tính tò mò, bất ngờ hoặc tương phản cao.
   - target_channel: Kênh phân phối chính (Facebook, TikTok, Threads, Shorts, YouTube...).
   - target_audience: Chân dung đối tượng độc giả mục tiêu.
   - core_message: Giá trị thực tiễn rút ra được sau bài viết.
4. Đảm bảo sự phân bổ cân bằng giữa các định dạng: bài sâu chuyên môn, bài chia sẻ kinh nghiệm, bài truyền cảm hứng và bài giới thiệu giải pháp/sản phẩm.

Bắt buộc trả về đúng định dạng WeeklyContentPlan."""


def run_planner_agent(
    trends_feed: List[Dict[str, Any]],
    brand_rules: List[str],
    week_id: str = DEFAULT_WEEK_ID,
) -> WeeklyContentPlan:
    """Thực thi logic cốt lõi của Agent 2 với structured output bắt buộc theo Rule 4."""
    llm = get_llm(model_type="core")
    structured_llm = llm.with_structured_output(WeeklyContentPlan)

    # Format bối cảnh từ trends_feed
    trends_context = "\n".join([
        f"- [{t.get('id', 'N/A')}] {t.get('topic', 'Chủ đề')} (Nguồn: {t.get('source_radar', 'Radar')}): {t.get('trend_summary', '')}"
        for t in trends_feed
    ]) if trends_feed else "Chưa có trends_feed. Tự đề xuất các góc bài hot nhất về AI & Automation."

    rules_context = "\n".join([f"- {r}" for r in brand_rules]) if brand_rules else "Tập trung giá trị thực tiễn, không lý thuyết suông."

    user_prompt = f"""Hãy lập ma trận kế hoạch nội dung tuần {week_id} gồm từ 5 đến 7 bài viết.

=== TRENDS RADAR ĐƯỢC CHỌN ===
{trends_context}

=== BRAND RULES CẦN TUÂN THỦ ===
{rules_context}

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

    plan = run_planner_agent(
        trends_feed=trends_feed,
        brand_rules=brand_rules,
        week_id=week_id,
    )

    plan_items_data = [item.model_dump() for item in plan.items]
    return {
        "content_plan": plan_items_data
    }
