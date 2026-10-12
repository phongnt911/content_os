"""Unit tests for Phase 2: LangGraph StateGraph, Checkpointer, and Human Touchpoint 1 interrupt/resume."""

import pytest
from langgraph.types import Command
from core.state import ContentOSState
from graph.workflow import create_content_os_graph


@pytest.fixture
def initial_state() -> ContentOSState:
    return {
        "week_id": "2026-W42",
        "brand_rules": ["Brand voice: Thực chiến, súc tích, giải quyết bài toán thật"],
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


def test_graph_interrupts_at_touchpoint_1(initial_state: ContentOSState):
    """Kiểm tra đồ thị chạy từ START và tạm dừng chính xác tại human_approve_plan."""
    app = create_content_os_graph()
    thread_config = {"configurable": {"thread_id": "thread_test_interrupt"}}

    # Chạy lần đầu
    app.invoke(initial_state, config=thread_config)

    # Lấy snapshot trạng thái hiện tại
    state_snapshot = app.get_state(thread_config)

    # Đồ thị phải đang tạm dừng và node tiếp theo là human_approve_plan
    assert "human_approve_plan" in state_snapshot.next

    # State đã có trends_feed và content_plan từ 2 Agent trước
    current_values = state_snapshot.values
    assert len(current_values["trends_feed"]) > 0
    assert 5 <= len(current_values["content_plan"]) <= 7
    assert current_values["plan_approved"] is False

    # Kiểm tra payload của interrupt
    assert len(state_snapshot.tasks) > 0
    task_interrupts = state_snapshot.tasks[0].interrupts
    assert len(task_interrupts) > 0
    payload = task_interrupts[0].value
    assert payload["touchpoint"] == 1
    assert payload["action"] == "human_approve_plan"
    assert payload["total_posts"] == len(current_values["content_plan"])


def test_graph_resumes_on_approved(initial_state: ContentOSState):
    """Kiểm tra khi User phê duyệt (approved=True), đồ thị tiếp tục sang plan_dispatch."""
    app = create_content_os_graph()
    thread_config = {"configurable": {"thread_id": "thread_test_approve_flow"}}

    # 1. Chạy tới điểm ngắt
    app.invoke(initial_state, config=thread_config)

    # 2. User duyệt kế hoạch
    resume_command = Command(resume={"approved": True, "note": "Kế hoạch tuần rất tốt!"})
    app.invoke(resume_command, config=thread_config)

    # 3. Kiểm tra: Nhánh Media dừng tại Human Touchpoint 2 (quay video)
    mid_snapshot = app.get_state(thread_config)
    assert "human_record_video" in mid_snapshot.next

    # 4. Cung cấp Touchpoint 2 để đồ thị chạy tới hoàn tất
    app.invoke(Command(resume={"raw_footage_url": "https://drive.google.com/test_clip"}), config=thread_config)
    final_snapshot = app.get_state(thread_config)
    assert len(final_snapshot.next) == 0  # Đã kết thúc chu trình

    final_values = final_snapshot.values
    assert final_values["plan_approved"] is True
    assert final_values["user_revision_note"] == "Kế hoạch tuần rất tốt!"
    assert "id" in final_values["selected_topic"]
    assert "angle" in final_values["selected_topic"]


def test_graph_ends_on_rejected(initial_state: ContentOSState):
    """Kiểm tra khi User từ chối (approved=False), đồ thị kết thúc thẳng tại END."""
    app = create_content_os_graph()
    thread_config = {"configurable": {"thread_id": "thread_test_reject_flow"}}

    # 1. Chạy tới điểm ngắt
    app.invoke(initial_state, config=thread_config)

    # 2. User từ chối kế hoạch
    resume_command = Command(resume={"approved": False, "note": "Chủ đề chưa phù hợp mục tiêu tháng này."})
    app.invoke(resume_command, config=thread_config)

    # 3. Kiểm tra đồ thị kết thúc và không vào plan_dispatch
    final_snapshot = app.get_state(thread_config)
    assert len(final_snapshot.next) == 0

    final_values = final_snapshot.values
    assert final_values["plan_approved"] is False
    assert final_values["user_revision_note"] == "Chủ đề chưa phù hợp mục tiêu tháng này."
    assert final_values["selected_topic"] == {}  # Không được dispatch
