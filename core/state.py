"""LinTech Content OS - State & Pydantic Schema Specification.

This module defines:
1. Strict Pydantic V2 models for structured outputs of all 16 agents.
2. The central `ContentOSState` (TypedDict) used by LangGraph nodes.
"""

from typing import List, Dict, Optional, Any, Annotated
from typing_extensions import TypedDict
import operator
from pydantic import BaseModel, Field


# ============================================================================
# 1. PYDANTIC SCHEMAS FOR STRUCTURED AGENT OUTPUTS
# ============================================================================

# --- Tầng 1: Planning Layer ---

class TrendTopic(BaseModel):
    """Schema cho từng chủ đề xu hướng từ Agent 1 (Research)."""
    id: str = Field(description="Mã định danh xu hướng, ví dụ: 'trend_01'")
    topic: str = Field(description="Tiêu đề hoặc chủ đề xu hướng")
    source_radar: str = Field(description="Nguồn quét tin tức / radar đối thủ")
    trend_summary: str = Field(description="Tóm tắt nội dung và bối cảnh vì sao đang hot")
    relevance_score: float = Field(ge=0.0, le=10.0, description="Điểm độ liên quan tới thương hiệu (0-10)")


class ResearchReport(BaseModel):
    """Đầu ra có cấu trúc của Agent 1 (Research)."""
    trends: List[TrendTopic] = Field(min_length=1, max_length=10, description="Danh sách các chủ đề xu hướng (thường là 5 chủ đề)")
    summary_insight: str = Field(description="Nhận định chung về bức tranh tuần")


class ContentPlanItem(BaseModel):
    """Brief cho từng bài viết trong kế hoạch tuần từ Agent 2 (Planner)."""
    id: str = Field(description="Mã bài viết, ví dụ: 'post_01'")
    angle: str = Field(description="Góc tiếp cận bài viết (Angle)")
    hook_concept: str = Field(description="Ý tưởng hook ban đầu mở bài")
    target_channel: str = Field(description="Kênh mục tiêu: Facebook, TikTok, Threads, Shorts...")
    target_audience: str = Field(default="Tech enthusiasts / Founders", description="Chân dung đối tượng độc giả")
    core_message: str = Field(description="Thông điệp giá trị cốt lõi")


class WeeklyContentPlan(BaseModel):
    """Đầu ra có cấu trúc của Agent 2 (Planner) lập lịch 5-7 bài/tuần."""
    week_id: str = Field(description="Mã tuần, ví dụ: '2026-W42'")
    plan_rationale: str = Field(description="Lý do sắp xếp và chiến lược tuần")
    items: List[ContentPlanItem] = Field(min_length=5, max_length=7, description="Ma trận 5-7 bài/tuần dạng brief")


# --- Tầng 2: Dây chuyền Chữ (Text Pipeline) ---

class OutlineStructure(BaseModel):
    """Đầu ra có cấu trúc của Agent 3 (Outline)."""
    topic_id: str = Field(description="Mã bài viết tương ứng")
    hook_variants: List[str] = Field(min_length=3, max_length=3, description="3 biến thể hook mở bài khác nhau")
    body_points: List[str] = Field(min_length=3, description="Các luận điểm chính của thân bài")
    call_to_action: str = Field(description="Lời kêu gọi hành động (CTA)")


class DraftReviewResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 5 (Review QA)."""
    draft_score: int = Field(ge=0, le=10, description="Thang điểm đánh giá từ 0 đến 10")
    draft_feedback: str = Field(description="Nhận xét chi tiết điểm mạnh và điểm cần cải thiện")
    strengths: List[str] = Field(default_factory=list, description="Các điểm tốt của bài viết")
    improvements: List[str] = Field(default_factory=list, description="Các điểm cụ thể cần viết lại nếu điểm < 8")
    approved: bool = Field(description="True nếu draft_score >= 8, ngược lại False")


class FactCheckResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 6 (Fact-check & Policy)."""
    has_policy_violation: bool = Field(description="True nếu phát hiện từ khóa vi phạm chính sách Meta/TikTok")
    policy_issues: List[str] = Field(default_factory=list, description="Chi tiết các vi phạm chính sách (nếu có)")
    spelling_errors: List[str] = Field(default_factory=list, description="Lỗi chính tả hoặc câu từ được phát hiện")
    verified_claims: List[str] = Field(default_factory=list, description="Các số liệu, khẳng định đã được đối chiếu")
    cleaned_draft: str = Field(description="Bản thảo hoàn thiện sau khi làm sạch lỗi")


class RepurposeThreadsResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 7 (Repurpose Threads)."""
    threads_posts: List[str] = Field(min_length=3, max_length=5, description="Chuỗi 3-5 post ngắn cho Threads")
    hook_post: str = Field(description="Post số 1 giật hook thu hút người xem")
    cta_post: str = Field(description="Post cuối cùng kêu gọi thảo luận hoặc follow")


class CarouselSlideItem(BaseModel):
    """Từng slide trong bộ kịch bản carousel của Agent 8."""
    slide_number: int = Field(ge=1, description="Số thứ tự slide")
    headline: str = Field(description="Tiêu đề slide")
    body_content: str = Field(description="Nội dung chính ngắn gọn súc tích")
    visual_layout_tip: str = Field(description="Gợi ý layout, icon hoặc hình minh họa")


class CarouselResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 8 (Carousel)."""
    slides: List[CarouselSlideItem] = Field(min_length=5, max_length=7, description="Kịch bản slide ảnh (5-7 trang)")
    cover_headline: str = Field(description="Tiêu đề trang bìa slide 1")
    last_slide_cta: str = Field(description="CTA slide cuối cùng")


# --- Tầng 3: Dây chuyền Video & Ảnh (Visual Pipeline) ---

class VideoSceneItem(BaseModel):
    """Phân đoạn kịch bản video của Agent 9."""
    scene_number: int = Field(ge=1, description="Số thứ tự phân cảnh")
    duration_seconds: int = Field(ge=1, le=20, description="Thời lượng phân cảnh (giây)")
    visual_cue: str = Field(description="Chỉ dẫn hình ảnh / động tác / góc máy")
    voice_prompter: str = Field(description="Lời thoại hiển thị trên máy nhắc chữ cho creator")


class VideoScriptResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 9 (Video Script)."""
    total_estimated_duration: int = Field(ge=30, le=55, description="Tổng thời lượng video (30-50s)")
    hook_opening: str = Field(description="Lời thoại hook 3 giây đầu tiên")
    scenes: List[VideoSceneItem] = Field(min_length=3, description="Danh sách các phân cảnh")
    cta_closing: str = Field(description="Lời thoại kêu gọi hành động cuối video")


class VideoReviewResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 11 (Review Video QA)."""
    video_approved: bool = Field(description="True nếu đạt chuẩn kỹ thuật, thời lượng < 60s")
    measured_duration: int = Field(description="Thời lượng video thực tế sau khi render (giây)")
    subtitle_synced: bool = Field(description="Phụ đề có khớp khẩu hình / audio không")
    technical_feedback: str = Field(description="Góp ý kỹ thuật cắt dựng, âm thanh, hiệu ứng")


class CoverPromptResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 12 (Cover Agent)."""
    prompt_3_4: str = Field(description="Prompt sinh ảnh bìa tỉ lệ 3:4 cho Facebook/Instagram")
    prompt_9_16: str = Field(description="Prompt sinh ảnh bìa tỉ lệ 9:16 cho TikTok/Reels")
    overlay_headline: str = Field(description="Chữ text nổi bật đè lên thumbnail")
    safe_zone_notes: str = Field(description="Lưu ý vị trí an toàn tránh bị che bởi UI nền tảng")


class ImageReviewResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 13 (Review Image QA)."""
    image_approved: bool = Field(description="True nếu thumbnail đạt chuẩn nhận diện thương hiệu")
    brand_guidelines_met: bool = Field(description="Logo, bảng màu, font chữ đúng quy chuẩn")
    safe_zone_valid: bool = Field(description="Chữ nằm trong vùng an toàn")
    feedback: str = Field(description="Nhận xét chi tiết")


# --- Tầng 4 & 5: Xuất bản, Vận hành, Phân tích ---

class PublishResult(BaseModel):
    """Đầu ra của Agent 14 (Publisher)."""
    published_links: Dict[str, str] = Field(description="Bản đồ kênh -> link bài đăng thực tế")
    published_status: str = Field(description="Trạng thái xuất bản (e.g., 'SUCCESS', 'PARTIAL')")


class CommentReplyResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 15 (Community Manager)."""
    matched_cta: str = Field(description="Từ khóa CTA mà độc giả đã comment")
    sentiment: str = Field(description="Sắc thái: Tích cực, Tiêu cực, Hỏi mua, Góp ý")
    auto_reply_text: str = Field(description="Câu trả lời tự động chuẩn phong cách thương hiệu")


class AnalyticsReportResult(BaseModel):
    """Đầu ra có cấu trúc của Agent 16 (Analytics & Optimization)."""
    winning_angles: List[str] = Field(description="Các góc bài viết (Angle) đạt tương tác cao nhất")
    learned_rules: List[str] = Field(description="Các bài học mới cần bổ sung vào brand_rules")
    metrics_summary: Dict[str, Any] = Field(description="Tổng hợp chỉ số reach, engagement, ctr...")


# ============================================================================
# 2. SHARED STATE SPECIFICATION (TypedDict)
# ============================================================================

class ContentOSState(TypedDict):
    """Trạng thái trung tâm được truyền qua tất cả các Node trong StateGraph."""
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
