"""Agent 15: Community Agent (Operations Layer).

Nhiệm vụ:
- Tiếp nhận thông điệp bài viết, kịch bản CTA và Brand Guidelines từ ContentOSState.
- Thiết lập chiến lược phản hồi tự động và seeding:
  + Nhận diện từ khóa CTA kích hoạt (e.g., 'WORKFLOW', 'AI', 'AUTOMATION').
  + Chuẩn bị danh sách bình luận gieo mầm (Seeding comments) kích thích thảo luận sâu.
  + Chuẩn bị kịch bản giải đáp tự động (FAQ Responses) theo các ý định phổ biến (Hỏi tài liệu, thắc mắc chi phí, phản biện).
- Xuất ra `CommunityStrategyResult` chuẩn Pydantic V2.
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ContentOSState, CommunityStrategyResult
from config import get_llm


COMMUNITY_SYSTEM_PROMPT = """Bạn là Agent 15 (Community Manager & Lead Conversion Specialist) thuộc LinTech Content OS.
Nhiệm vụ của bạn:
1. Phân tích nội dung bài viết đã xuất bản và lời kêu gọi hành động (CTA).
2. Xây dựng chiến lược chăm sóc bình luận và điều hướng độc giả:
   - target_cta_keyword: Từ khóa chính độc giả cần để lại dưới comment (viết hoa, ngắn gọn, e.g. WORKFLOW, AUTOMATE).
   - lead_magnet_url: Link landing page hoặc tài liệu hướng dẫn thực chiến.
   - seeding_comments: Tối thiểu 2 bình luận mồi giả lập chuyên gia thảo luận để kích hoạt thuật toán mạng xã hội.
   - faq_replies: Tối thiểu 2 kịch bản trả lời mẫu có tâm, đúng tinh thần thực chiến, lồng ghép link chuyển đổi tự nhiên.

Bắt buộc trả về đúng định dạng CommunityStrategyResult."""


def run_community_agent(
    content_draft: str,
    selected_topic: Dict[str, Any],
    brand_rules: List[str],
) -> CommunityStrategyResult:
    """Thực thi logic xây dựng chiến lược bình luận của Agent 15 với structured output."""
    llm = get_llm(model_type="fast")
    structured_llm = llm.with_structured_output(CommunityStrategyResult)

    angle = selected_topic.get("angle", "Thực chiến công nghệ & AI")
    target_channel = selected_topic.get("target_channel", "Đa kênh")
    rules_context = "\n- ".join(brand_rules) if brand_rules else "Thân thiện, giải quyết triệt để vấn đề, không spam."

    user_prompt = f"""Hãy xây dựng chiến lược quản lý bình luận và điều hướng CTA cho bài viết sau:
- Kênh chính: {target_channel}
- Góc bài viết: {angle}
- Trích đoạn nội dung bài:
\"\"\"{content_draft[:600]}\"\"\"

Brand Voice Guidelines:
- {rules_context}

Xuất ra cấu trúc CommunityStrategyResult hoàn chỉnh."""

    messages = [
        SystemMessage(content=COMMUNITY_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    strategy: CommunityStrategyResult = structured_llm.invoke(messages)
    return strategy


def community_node(state: ContentOSState) -> Dict[str, Any]:
    """LangGraph Node tương thích cho Agent 15.
    
    Nhận `state: ContentOSState`, sinh kịch bản chăm sóc cộng đồng.
    """
    draft = state.get("fact_checked_draft") or state.get("raw_draft", "")
    selected_topic = state.get("selected_topic", {})
    brand_rules = state.get("brand_rules", [])

    strategy = run_community_agent(draft, selected_topic, brand_rules)

    return {}
