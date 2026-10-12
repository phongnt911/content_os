"""Unit tests for Phase 4: Media Pipeline Agents, Human Touchpoint 2, and Parallel DAG Fork-Join."""

import pytest
from langgraph.types import Command
from core.state import ContentOSState
from agents.media_pipeline.script_agent import script_node, run_script_agent
from agents.media_pipeline.video_editor import video_editing_node, VideoEditingService
from agents.media_pipeline.review_video import review_video_node, run_review_video_agent
from agents.media_pipeline.cover_agent import cover_agent_node, run_cover_agent
from agents.media_pipeline.review_image import review_image_node, run_review_image_agent
from graph.edges import route_after_video_review
from graph.workflow import create_content_os_graph


@pytest.fixture
def sample_topic():
    return {
        "id": "post_01",
        "angle": "Tự động hóa sản xuất video đa kênh với AI",
        "hook_concept": "Đừng mất cả ngày để quay và cắt dựng video ngắn nữa",
        "target_channel": "TikTok",
        "target_audience": "Founders & Creators",
        "core_message": "Quy trình AI giúp render video và phụ đề trong 30 giây.",
    }


def test_video_script_agent(sample_topic):
    """Kiểm tra Agent 9 xuất kịch bản video ngắn 30-50s chuẩn cấu trúc."""
    script_res = run_script_agent(sample_topic, ["Brand: Năng lượng, thực chiến"])
    assert 30 <= script_res.total_estimated_duration <= 55
    assert len(script_res.hook_opening) > 0
    assert len(script_res.scenes) >= 3
    assert len(script_res.cta_closing) > 0


def test_video_editor_service(sample_topic):
    """Kiểm tra Agent 10 xử lý dựng video qua VideoEditingService."""
    service = VideoEditingService()
    mock_script = {
        "total_estimated_duration": 45,
        "hook_opening": "Hook mở bài",
        "scenes": [],
    }
    result = service.process_and_render(
        raw_footage_url="https://drive.google.com/file/d/test_footage/view",
        script=mock_script,
    )
    assert result["status"] == "RENDER_SUCCESS"
    assert "rendered_video_url" in result
    assert result["video_duration"] < 60


def test_video_review_agent():
    """Kiểm tra Agent 11 thẩm định thông số kỹ thuật video."""
    res = run_review_video_agent(
        video_url="https://cdn.lintech.media/sample.mp4",
        duration=45,
        script={"hook_opening": "Hook mở bài"},
    )
    assert res.measured_duration == 45
    assert res.subtitle_synced is True


def test_video_review_routing_guard():
    """Kiểm tra Loop Breaker của vòng lặp render video (Max 1 lần)."""
    # Lỗi và chưa render lại lần nào -> Render lại
    mock_state_retry: ContentOSState = {"video_approved": False, "video_revision_count": 0}  # type: ignore
    assert route_after_video_review(mock_state_retry) == "video_editing"

    # Đã render lại 1 lần -> Thoát loop đi tiếp
    mock_state_max: ContentOSState = {"video_approved": False, "video_revision_count": 1}  # type: ignore
    assert route_after_video_review(mock_state_max) == "generate_cover_image"

    # Đạt chuẩn -> Đi tiếp
    mock_state_pass: ContentOSState = {"video_approved": True, "video_revision_count": 0}  # type: ignore
    assert route_after_video_review(mock_state_pass) == "generate_cover_image"


def test_cover_and_review_image_agents(sample_topic):
    """Kiểm tra Agent 12 sinh prompt ảnh bìa và Agent 13 duyệt nhận diện thương hiệu."""
    script_data = {"hook_opening": "AI Dựng Video Trong 30 Giây"}
    cover_res = run_cover_agent(sample_topic, script_data, ["Brand: Gam màu neon hiện đại"])

    assert len(cover_res.prompt_3_4) > 0
    assert len(cover_res.prompt_9_16) > 0
    assert len(cover_res.overlay_headline) > 0

    img_review = run_review_image_agent("https://cdn.lintech.media/thumb.jpg", [])
    assert img_review.image_approved is True


def test_full_dag_fork_join_workflow():
    """Kiểm tra đồ thị chạy song song 2 nhánh Text & Visual qua cả 2 Human Touchpoints và hội tụ tại join_node."""
    app = create_content_os_graph()
    thread_config = {"configurable": {"thread_id": "thread_dag_fork_join"}}

    initial_state: ContentOSState = {
        "week_id": "2026-W42",
        "brand_rules": ["Brand voice: Thực chiến, tốc độ"],
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

    # 1. Chạy tới Human Touchpoint 1 (Duyệt Plan)
    app.invoke(initial_state, config=thread_config)
    snapshot_1 = app.get_state(thread_config)
    assert "human_approve_plan" in snapshot_1.next

    # 2. Duyệt Plan -> Đồ thị kích hoạt song song 2 nhánh, nhánh Video dừng tại Human Touchpoint 2
    app.invoke(Command(resume={"approved": True}), config=thread_config)
    snapshot_2 = app.get_state(thread_config)
    assert "human_record_video" in snapshot_2.next

    # 3. Nạp link video raw vào Touchpoint 2
    user_footage = "https://drive.google.com/file/d/creator_raw_clip_1080p/view"
    app.invoke(Command(resume={"raw_footage_url": user_footage}), config=thread_config)

    # 4. Kiểm tra đồ thị hoàn thành cả 2 nhánh và hội tụ tại join_node
    final_snapshot = app.get_state(thread_config)
    assert len(final_snapshot.next) == 0  # Đã hoàn tất luồng

    vals = final_snapshot.values
    # Kiểm tra Nhánh Chữ
    assert len(vals["raw_draft"]) > 0
    assert 3 <= len(vals["threads_posts"]) <= 5
    assert 5 <= len(vals["carousel_slides"]) <= 7

    # Kiểm tra Nhánh Video & Ảnh
    assert len(vals["video_script"]) > 0
    assert vals["raw_footage_url"] == user_footage
    assert "rendered_video_url" in vals
    assert vals["video_duration"] < 60
    assert "cover_image_url" in vals

    # Kiểm tra Hội tụ tại join_node
    assert vals["total_cycle_count"] >= 1
