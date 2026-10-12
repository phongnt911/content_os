# LINTECH CONTENT OS - SYSTEM ARCHITECTURE & IMPLEMENTATION SPEC

## 1. PROJECT OVERVIEW
- **Tên dự án:** LinTech Content OS (Multi-Agent Multi-Channel Content Production & Distribution)
- **Framework cốt lõi:** LangGraph (StateGraph, Checkpointer, Human-in-the-loop Interrupts)
- **Mô hình kiến trúc:** Đồ thị trạng thái có chu trình (Cyclic StateGraph) kết hợp phân nhánh song song (DAG Fork-Join).
- **Nguyên lý cốt lõi:** 
  1. Tự động hóa tối đa với 16 AI Agents chuyên trách.
  2. Con người là chốt chặn quyết định (Human-in-the-loop) tại đúng 3 điểm: Duyệt Plan tuần, Quay video raw, và Phê duyệt gói nội dung hoàn chỉnh trước khi đăng.
  3. Cơ chế tự sửa sai (Self-Correction Loop) với giới hạn số lần lặp (Loop Breaker / Recursion Guards) chống tràn token.

---

## 2. DIRECTORY TREE CONVENTION
Mọi code tạo ra PHẢI tuân thủ nghiêm ngặt cấu trúc modular:

```text
content_os/
├── config.py                     # Quản lý LLM instances (LLM_CORE, LLM_FAST) & env vars
├── requirements.txt              # Thư viện phụ thuộc
├── .env                          # API keys
├── PROJECT_SPEC.md               # Tài liệu đặc tả này
├── core/
│   ├── __init__.py
│   ├── state.py                  # TypedDict ContentOSState & Pydantic Schemas
│   └── checkpointer.py           # SQLite/Memory checkpointer cho LangGraph
├── agents/
│   ├── planning/
│   │   ├── research_agent.py     # Agent 1: Quét xu hướng, tin tức
│   │   └── planner_agent.py      # Agent 2: Lập ma trận 5-7 bài/tuần
│   ├── text_pipeline/
│   │   ├── outline_agent.py      # Agent 3: Dàn ý Hook - Body - CTA
│   │   ├── writer_agent.py       # Agent 4: Chấp bút chuẩn Brand Voice
│   │   ├── review_agent.py       # Agent 5: Chấm điểm (0-10) & đánh giá
│   │   ├── factcheck_agent.py    # Agent 6: Rà soát chính tả, số liệu
│   │   ├── repurpose_agent.py    # Agent 7: Tách chuỗi Threads (3-5 post)
│   │   └── carousel_agent.py     # Agent 8: Soạn kịch bản slide (5-7 trang)
│   ├── media_pipeline/
│   │   ├── script_agent.py       # Agent 9: Kịch bản video 30-50s + visual cues
│   │   ├── video_editor.py       # Agent 10: Auto-cut, sub, B-roll, SFX API mock/tool
│   │   ├── review_video.py       # Agent 11: Kiểm định thời lượng & phụ đề
│   │   ├── cover_agent.py        # Agent 12: Prompt & layout ảnh bìa 3:4 / 9:16
│   │   └── review_image.py       # Agent 13: Duyệt nhận diện thương hiệu
│   └── operations/
│       ├── publisher_agent.py    # Agent 14: API đăng đa kênh (FB, TikTok, Threads, Shorts)
│       ├── community_agent.py    # Agent 15: Phân loại & trả lời bình luận theo CTA
│       └── analytics_agent.py    # Agent 16: Phân tích chỉ số tuần & tự cập nhật Brand Brain
├── graph/
│   ├── __init__.py
│   ├── nodes.py                  # Đóng gói các hàm node gọi Agent
│   ├── edges.py                  # Các hàm điều kiện rẽ nhánh & vòng lặp
│   └── workflow.py               # Biên dịch StateGraph và Compile App
└── main.py                       # CLI Test & Stream Runner
```

---

## 3. SHARED STATE SPECIFICATION (core/state.py)
Tất cả các node trong LangGraph PHẢI giao tiếp qua cấu trúc ContentOSState dưới đây:

```python
from typing import List, Dict, Optional, Any, Annotated
from typing_extensions import TypedDict
import operator

class ContentOSState(TypedDict):
    # 1. Metadata & Memory
    week_id: str
    brand_rules: Annotated[List[str], operator.add]
    
    # 2. Chặng 1: Planning
    trends_feed: List[Dict[str, Any]]
    content_plan: List[Dict[str, Any]]
    plan_approved: bool                  # Human Touchpoint 1
    
    # 3. Chặng 2A: Dây chuyền Chữ
    selected_topic: Dict[str, Any]
    outline: Dict[str, Any]
    raw_draft: str
    draft_score: int                     # Thang điểm 0 - 10
    draft_feedback: str                  # Nhận xét từ Agent 5
    text_revision_count: int             # Guard: Max 2
    fact_checked_draft: str
    threads_posts: List[str]
    carousel_slides: List[Dict[str, Any]]
    
    # 4. Chặng 2B: Dây chuyền Video & Ảnh
    video_script: Dict[str, Any]
    raw_footage_url: Optional[str]       # Human Touchpoint 2 (User quay video thả Drive)
    rendered_video_url: Optional[str]
    video_duration: int                  # Yêu cầu < 60s
    video_approved: bool
    video_revision_count: int            # Guard: Max 1
    cover_image_url: Optional[str]
    image_approved: bool
    image_revision_count: int            # Guard: Max 2
    
    # 5. Chặng 3: Xuất bản & Điều hành
    final_package_approved: bool         # Human Touchpoint 3 (Duyệt trọn bộ)
    user_revision_note: Optional[str]
    total_cycle_count: int               # Guard: Max 4
    published_links: Dict[str, str]
    
    # 6. Chặng 4: Đo lường & Vòng học tuần
    weekly_metrics: Dict[str, Any]
```

