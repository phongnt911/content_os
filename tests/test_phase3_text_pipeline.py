"""Unit tests for Phase 3: Text Pipeline Agents & Self-Correction Loop."""

import pytest
from langgraph.types import Command
from core.state import ContentOSState
from agents.text_pipeline.outline_agent import outline_node, run_outline_agent
from agents.text_pipeline.writer_agent import writer_node, run_writer_agent
from agents.text_pipeline.review_agent import review_node, run_review_agent
from agents.text_pipeline.factcheck_agent import factcheck_node, run_factcheck_agent
from agents.text_pipeline.repurpose_agent import repurpose_node, run_repurpose_agent
from agents.text_pipeline.carousel_agent import carousel_node, run_carousel_agent
from graph.edges import route_after_text_review
from graph.workflow import create_content_os_graph


@pytest.fixture
def sample_topic():
    return {
        "id": "post_01",
        "angle": "Chiến lược tự động hóa quy trình sản xuất nội dung với Multi-Agent",
        "hook_concept": "Đừng viết content thủ công nếu bạn không muốn kiệt sức",
        "target_channel": "Facebook",
        "target_audience": "Founders & Creators",
        "core_message": "Hệ thống LangGraph giúp tăng 5x sản lượng mà vẫn chuẩn Brand Voice.",
    }


def test_outline_agent(sample_topic):
    """Kiểm tra Agent 3 xuất đúng 3 hook variants, body points và CTA."""
    outline = run_outline_agent(sample_topic, ["Brand: Thực chiến, súc tích"])
    assert len(outline.hook_variants) == 3
    assert len(outline.body_points) >= 3
    assert len(outline.call_to_action) > 0


def test_writer_and_review_agent(sample_topic):
    """Kiểm tra Agent 4 chấp bút và Agent 5 chấm điểm với structured output."""
    outline = run_outline_agent(sample_topic, [])
    outline_dict = outline.model_dump()

    # Agent 4 viết bài
    draft = run_writer_agent(outline_dict, ["Văn phong gãy gọn"])
    assert len(draft) > 50

    # Agent 5 chấm điểm
    review = run_review_agent(draft, outline_dict, [])
    assert 0 <= review.draft_score <= 10
    assert len(review.draft_feedback) > 0


def test_self_correction_routing_guard():
    """Kiểm tra logic điều kiện rẽ nhánh và Loop Breaker của Agent 5."""
    # Điểm thấp (< 8) và chưa hết số lần sửa (< 2) -> Phải lặp lại viết lại
    mock_state_retry: ContentOSState = {"draft_score": 6, "text_revision_count": 1}  # type: ignore
    assert route_after_text_review(mock_state_retry) == "writer"

    # Điểm thấp (< 8) nhưng ĐÃ ĐỦ 2 lần sửa -> Thoát loop sang fact_check
    mock_state_max_revisions: ContentOSState = {"draft_score": 7, "text_revision_count": 2}  # type: ignore
    assert route_after_text_review(mock_state_max_revisions) == "fact_check"

    # Điểm cao (>= 8) -> Đi tiếp sang fact_check
    mock_state_pass: ContentOSState = {"draft_score": 9, "text_revision_count": 1}  # type: ignore
    assert route_after_text_review(mock_state_pass) == "fact_check"


def test_factcheck_repurpose_and_carousel(sample_topic):
    """Kiểm tra Agent 6, 7, 8 hoàn thiện chuỗi sản xuất Text."""
    raw_text = "Dừng viết content bằng tay nếu bạn không muốn kiệt sức. Áp dụng AI Multi-Agent ngay hôm nay!"

    # Agent 6: Fact check
    fc_res = run_factcheck_agent(raw_text)
    assert len(fc_res.cleaned_draft) > 0

    # Agent 7: Threads Series
    threads_res = run_repurpose_agent(fc_res.cleaned_draft)
    assert 3 <= len(threads_res.threads_posts) <= 5

    # Agent 8: Carousel slides
    carousel_res = run_carousel_agent(fc_res.cleaned_draft)
    assert 5 <= len(carousel_res.slides) <= 7


def test_full_text_pipeline_in_graph():
    """Kiểm tra toàn bộ dây chuyền Chữ chạy tự động xuyên suốt trong StateGraph."""
    app = create_content_os_graph()
    thread_config = {"configurable": {"thread_id": "thread_full_text_pipeline"}}

    initial_state: ContentOSState = {
        "week_id": "2026-W42",
        "brand_rules": ["Brand voice: Thực chiến, truyền cảm hứng"],
        "trends_feed": [],
        "content_plan": [],
        "plan_approved": False,
        "selected_topic": {},
        "outline": {},
        "raw_draft": "",
        "draft_score": 0,
        "draft_feedback": "",
        "text_revision_count": 0,
        "fact_checked_draft": "",
        "threads_posts": [],
        "carousel_slides": [],
        "video_script": {},
        "raw_footage_url": None,
        "rendered_video_url": None,
        "video_duration": 0,
        "video_approved": False,
        "video_revision_count": 0,
        "cover_image_url": None,
        "image_approved": False,
        "image_revision_count": 0,
        "final_package_approved": False,
        "user_revision_note": None,
        "total_cycle_count": 0,
        "published_links": {},
        "weekly_metrics": {},
    }

    # 1. Chạy tới Human Touchpoint 1
    app.invoke(initial_state, config=thread_config)
    snapshot = app.get_state(thread_config)
    assert "human_approve_plan" in snapshot.next

    # 2. User duyệt kế hoạch -> Nhánh Text chạy và nhánh Media dừng tại Human Touchpoint 2
    app.invoke(Command(resume={"approved": True}), config=thread_config)
    mid_snapshot = app.get_state(thread_config)
    assert "human_record_video" in mid_snapshot.next

    # 3. User cung cấp footage video để hội tụ hoàn toàn
    app.invoke(Command(resume={"raw_footage_url": "https://test.video/clip.mp4"}), config=thread_config)
    final_snapshot = app.get_state(thread_config)
    assert len(final_snapshot.next) == 0  # Đã chạy tới END thành công

    vals = final_snapshot.values
    assert vals["plan_approved"] is True
    assert "hook_variants" in vals["outline"]
    assert len(vals["raw_draft"]) > 0
    assert vals["draft_score"] >= 0
    assert len(vals["fact_checked_draft"]) > 0
    assert 3 <= len(vals["threads_posts"]) <= 5
    assert 5 <= len(vals["carousel_slides"]) <= 7
