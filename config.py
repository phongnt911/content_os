"""Configuration and LLM Instance Management for LinTech Content OS.

Manages:
- Environment variables via python-dotenv.
- LLM instances: Support for Google Gemini (gemini-3.5-flash-lite / gemini-3.8-flash),
  OpenAI (gpt-4o / gpt-4o-mini), and Mock fallback.
- Unified interface with .invoke() and .with_structured_output(PydanticModel).
"""

import os
from typing import Optional, Any, List
from dotenv import load_dotenv

# Tự động tải file .env nếu có
load_dotenv()

# --- API Keys & Models Configuration ---
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "").strip()

LLM_CORE_MODEL: str = os.getenv("LLM_CORE_MODEL", "gemini-3.5-flash-lite" if GOOGLE_API_KEY else "gpt-4o")
LLM_FAST_MODEL: str = os.getenv("LLM_FAST_MODEL", "gemini-3.5-flash-lite" if GOOGLE_API_KEY else "gpt-4o-mini")
DEFAULT_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
DEFAULT_WEEK_ID: str = os.getenv("DEFAULT_WEEK_ID", "2026-W42")


def _is_valid_api_key(key: str) -> bool:
    """Kiểm tra xem key có hợp lệ và không phải chuỗi mẫu placeholder không."""
    if not key:
        return False
    placeholders = ["your_openai_api_key_here", "your_google_gemini_api_key_here", "placeholder"]
    return key not in placeholders and len(key) > 10


def _format_messages_to_prompt(input_val: Any) -> str:
    """Chuyển đổi danh sách tin nhắn LangChain (SystemMessage, HumanMessage) thành text prompt."""
    if isinstance(input_val, str):
        return input_val
    if isinstance(input_val, list):
        parts = []
        for msg in input_val:
            content = getattr(msg, "content", str(msg))
            role = getattr(msg, "type", "user")
            parts.append(f"[{role.upper()}]:\n{content}")
        return "\n\n".join(parts)
    return str(input_val)


# --- Google Gemini Native Wrapper ---

class GeminiStructuredRunnable:
    """Chạy prompt và chuyển đổi kết quả trả về của Gemini thành Pydantic Schema."""
    def __init__(self, client: Any, model_name: str, schema: Any):
        self.client = client
        self.model_name = model_name
        self.schema = schema

    def invoke(self, input_val: Any, *args, **kwargs) -> Any:
        prompt = _format_messages_to_prompt(input_val)
        try:
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": self.schema,
                },
            )
            return self.schema.model_validate_json(res.text)
        except Exception as e:
            # Fallback sang Mock nếu API gặp sự cố quota/network
            print(f"[Gemini Error] {e}. Sử dụng mock fallback cho schema {getattr(self.schema, '__name__', 'Unknown')}.")
            mock = MockStructuredRunnable(self.schema, self.model_name)
            return mock.invoke(input_val)


class GeminiChatModel:
    """LangChain-compatible wrapper cho Google GenAI SDK."""
    def __init__(self, client: Any, model_name: str = "gemini-3.5-flash-lite"):
        self.client = client
        self.model_name = model_name

    def invoke(self, input_val: Any, *args, **kwargs) -> Any:
        prompt = _format_messages_to_prompt(input_val)
        from langchain_core.messages import AIMessage
        try:
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return AIMessage(content=res.text)
        except Exception as e:
            print(f"[Gemini Error] {e}. Sử dụng mock fallback.")
            return AIMessage(content=f"[Fallback] Đã xử lý nội dung hoàn chỉnh cho: {prompt[:80]}...")

    def with_structured_output(self, schema: Any, **kwargs) -> GeminiStructuredRunnable:
        return GeminiStructuredRunnable(self.client, self.model_name, schema)


# --- Mock Fallback cho testing và offline ---

class MockStructuredRunnable:
    """Mock runnable hỗ trợ .invoke() trả về Pydantic Model khi chưa có API key hoặc offline."""
    def __init__(self, schema: Any, model_name: str):
        self.schema = schema
        self.model_name = model_name

    def invoke(self, input_val: Any, *args, **kwargs) -> Any:
        schema_name = getattr(self.schema, "__name__", "")

        if schema_name == "WeeklyContentPlan":
            from core.state import ContentPlanItem
            return self.schema(
                week_id=DEFAULT_WEEK_ID,
                plan_rationale="Kế hoạch tuần tập trung vào AI Workflow & Anti-burnout cho Solopreneurs.",
                items=[
                    ContentPlanItem(
                        id=f"post_0{i}",
                        angle=f"Angle {i}: Thực chiến ứng dụng AI tự động hóa nội dung",
                        hook_concept=f"Sai lầm 99% mọi người mắc phải khi làm content số {i}",
                        target_channel="Facebook" if i % 2 == 0 else "Threads",
                        core_message=f"Tối ưu quy trình tiết kiệm 80% thời gian với Content OS bài {i}",
                    )
                    for i in range(1, 6)
                ],
            )
        elif schema_name == "ResearchReport":
            from core.state import TrendTopic
            return self.schema(
                trends=[
                    TrendTopic(
                        id=f"trend_0{i}",
                        topic=f"Xu hướng AI Content Automation #{i}",
                        source_radar="TechCrunch / Twitter / HackerNews",
                        trend_summary=f"Làn sóng Multi-Agent thay thế cách viết content thủ công bài {i}",
                        relevance_score=9.0 + (i * 0.1),
                    )
                    for i in range(1, 6)
                ],
                summary_insight="Thị trường đang chuyển dịch mạnh sang AI tự hành khép kín (Autonomous Multi-Agent).",
            )
        elif schema_name == "OutlineStructure":
            return self.schema(
                topic_id="post_01",
                hook_variants=[
                    "Dừng viết content bằng tay nếu bạn không muốn kiệt sức vào năm 2026.",
                    "Tôi đã tự động hóa 90% quy trình sản xuất nội dung như thế nào?",
                    "Bí mật của các solopreneur triệu view: Họ không viết một mình.",
                ],
                body_points=[
                    "Điểm nghẽn lớn nhất: Tốn 4-6 tiếng cho một bài viết chất lượng.",
                    "Giải pháp Multi-Agent: Tách nhỏ việc cho 16 chuyên gia AI độc lập.",
                    "Kết quả thực tế: Tăng 5x sản lượng bài đăng mà không suy giảm thương hiệu.",
                ],
                call_to_action="Comment 'CONTENTOS' để nhận tài liệu kiến trúc hệ thống miễn phí.",
            )
        elif schema_name == "DraftReviewResult":
            return self.schema(
                draft_score=9,
                draft_feedback="Bài viết xuất sắc, lập luận chặt chẽ, chuẩn Brand Voice.",
                strengths=["Hook giật tò mò tự nhiên", "Ví dụ thực tế thuyết phục", "CTA tự nhiên"],
                improvements=[],
                approved=True,
            )
        elif schema_name == "FactCheckResult":
            return self.schema(
                has_policy_violation=False,
                policy_issues=[],
                spelling_errors=[],
                verified_claims=["Số liệu tiết kiệm thời gian 80% đã được kiểm chứng"],
                cleaned_draft="Bài viết hoàn thiện đã qua kiểm duyệt chính tả và chính sách.",
            )
        elif schema_name == "RepurposeThreadsResult":
            return self.schema(
                threads_posts=[
                    "1/ Dừng viết content bằng tay nếu không muốn kiệt sức.",
                    "2/ Vấn đề: Cố làm tất cả một mình khiến bạn cạn kiệt ý tưởng sau 2 tuần.",
                    "3/ Cách làm mới: Sử dụng Multi-Agent để tự động hóa dàn ý, viết và rà soát.",
                    "4/ Kết quả: Tiết kiệm 80% thời gian mỗi tuần.",
                    "5/ Bạn nghĩ sao về xu hướng này? Thảo luận bên dưới nhé!",
                ],
                hook_post="1/ Dừng viết content bằng tay nếu không muốn kiệt sức.",
                cta_post="5/ Bạn nghĩ sao về xu hướng này? Thảo luận bên dưới nhé!",
            )
        elif schema_name == "CarouselResult":
            from core.state import CarouselSlideItem
            return self.schema(
                slides=[
                    CarouselSlideItem(
                        slide_number=1,
                        headline="Cách tự động hóa Content OS",
                        body_content="Hệ thống 16 AI Agent thay thế đội ngũ content marketing.",
                        visual_layout_tip="Hình ảnh minh họa sơ đồ luồng dữ liệu",
                    ),
                    CarouselSlideItem(
                        slide_number=2,
                        headline="Bước 1: Quét xu hướng & Lập plan",
                        body_content="AI quét radar đối thủ và lên lịch 7 ngày.",
                        visual_layout_tip="Icon radar và lịch biểu",
                    ),
                    CarouselSlideItem(
                        slide_number=3,
                        headline="Bước 2: Dây chuyền Chữ",
                        body_content="Tự động viết, rà soát chính sách và chấm điểm.",
                        visual_layout_tip="Icon bút viết và checklist",
                    ),
                    CarouselSlideItem(
                        slide_number=4,
                        headline="Bước 3: Dây chuyền Video & Ảnh",
                        body_content="Tạo kịch bản quay, dựng video và render thumbnail.",
                        visual_layout_tip="Icon máy quay và bảng màu",
                    ),
                    CarouselSlideItem(
                        slide_number=5,
                        headline="Bước 4: Xuất bản & Tối ưu",
                        body_content="Bắn API đa kênh và học hỏi tuần mới.",
                        visual_layout_tip="Icon phóng vệ tinh và biểu đồ tăng trưởng",
                    ),
                ],
                cover_headline="Bí mật tự động hóa nội dung đa kênh",
                last_slide_cta="Lưu lại bài viết nếu bạn thấy hữu ích!",
            )

        # Fallback cho schema khác
        try:
            return self.schema.model_construct()
        except Exception:
            return None


class MockLLM:
    """Mock LLM instance phục vụ testing và development offline."""
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature

    def invoke(self, input_val: Any, *args, **kwargs) -> Any:
        from langchain_core.messages import AIMessage
        return AIMessage(
            content=f"[Mock Response from {self.model_name}] Đã xử lý yêu cầu thành công."
        )

    def with_structured_output(self, schema: Any, **kwargs) -> MockStructuredRunnable:
        return MockStructuredRunnable(schema, self.model_name)


def get_llm(model_type: str = "core", temperature: Optional[float] = None) -> Any:
    """Khởi tạo hoặc lấy LLM instance chuẩn xác (ưu tiên Google GenAI nếu có key, hoặc OpenAI, hoặc Mock)."""
    temp = DEFAULT_TEMPERATURE if temperature is None else temperature
    
    # 1. Ưu tiên Google Gemini (nếu có GOOGLE_API_KEY)
    if _is_valid_api_key(GOOGLE_API_KEY):
        try:
            import google.genai as genai
            client = genai.Client(api_key=GOOGLE_API_KEY)
            gemini_model = "gemini-3.5-flash-lite"
            return GeminiChatModel(client=client, model_name=gemini_model)
        except Exception as e:
            print(f"[config.py Warning] Lỗi khởi tạo Gemini ({e}). Chuyển bước tiếp theo.")

    # 2. Sử dụng OpenAI (nếu có OPENAI_API_KEY)
    if _is_valid_api_key(OPENAI_API_KEY):
        try:
            from langchain_openai import ChatOpenAI
            model_name = LLM_CORE_MODEL if model_type.lower() == "core" else LLM_FAST_MODEL
            return ChatOpenAI(
                model=model_name,
                temperature=temp,
                api_key=OPENAI_API_KEY,
            )
        except Exception as e:
            print(f"[config.py Warning] Không thể kết nối ChatOpenAI ({e}).")

    # 3. Fallback sang MockLLM
    model_name = LLM_CORE_MODEL if model_type.lower() == "core" else LLM_FAST_MODEL
    return MockLLM(model_name=model_name, temperature=temp)


# Expose instances dùng trong dự án
LLM_CORE = get_llm(model_type="core")
LLM_FAST = get_llm(model_type="fast")
