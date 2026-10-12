"""Configuration and LLM Instance Management for LinTech Content OS.

Manages:
- Environment variables via python-dotenv.
- LLM instances: LLM_CORE (e.g. gpt-4o) and LLM_FAST (e.g. gpt-4o-mini).
- Robust fallback/mock capability for offline development and testing.
"""

import os
from typing import Optional, Any
from dotenv import load_dotenv

# Tự động tải file .env nếu có
load_dotenv()

# --- API Keys & Models Configuration ---
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "").strip()

LLM_CORE_MODEL: str = os.getenv("LLM_CORE_MODEL", "gpt-4o")
LLM_FAST_MODEL: str = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
DEFAULT_WEEK_ID: str = os.getenv("DEFAULT_WEEK_ID", "2026-W42")


def _is_valid_api_key(key: str) -> bool:
    """Kiểm tra xem key có hợp lệ và không phải chuỗi mẫu placeholder không."""
    if not key:
        return False
    placeholders = ["your_openai_api_key_here", "your_google_gemini_api_key_here", "placeholder"]
    return key not in placeholders and len(key) > 10


class MockStructuredRunnable:
    """Mock runnable hỗ trợ .invoke() trả về Pydantic Model khi chưa có API key thật."""
    def __init__(self, schema: Any, model_name: str):
        self.schema = schema
        self.model_name = model_name

    def invoke(self, input_val: Any, *args, **kwargs) -> Any:
        # Nếu schema là WeeklyContentPlan (Agent 2)
        if hasattr(self.schema, "__name__") and self.schema.__name__ == "WeeklyContentPlan":
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
        # Nếu schema là ResearchReport (Agent 1)
        elif hasattr(self.schema, "__name__") and self.schema.__name__ == "ResearchReport":
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
        # Fallback cho schema pydantic khác
        try:
            return self.schema.model_construct()
        except Exception:
            return None


class MockLLM:
    """Mock LLM instance phục vụ testing và development môi trường offline."""
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
    """Khởi tạo hoặc lấy LLM instance chuẩn xác (LLM_CORE hoặc LLM_FAST).
    
    Args:
        model_type: "core" (gpt-4o) hoặc "fast" (gpt-4o-mini)
        temperature: Độ biến thiên (mặc định theo DEFAULT_TEMPERATURE)
    """
    temp = DEFAULT_TEMPERATURE if temperature is None else temperature
    model_name = LLM_CORE_MODEL if model_type.lower() == "core" else LLM_FAST_MODEL
    
    if _is_valid_api_key(OPENAI_API_KEY):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name,
                temperature=temp,
                api_key=OPENAI_API_KEY,
            )
        except Exception as e:
            print(f"[config.py Warning] Không thể kết nối ChatOpenAI ({e}). Chuyển sang MockLLM.")
            return MockLLM(model_name=model_name, temperature=temp)
    else:
        # Nếu chưa cấu hình OPENAI_API_KEY thật, trả về MockLLM để test pipeline
        return MockLLM(model_name=model_name, temperature=temp)


# Expose instances dùng trong dự án
LLM_CORE = get_llm(model_type="core")
LLM_FAST = get_llm(model_type="fast")
