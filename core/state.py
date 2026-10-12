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
