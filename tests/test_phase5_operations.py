"""Unit and Integration Tests for Phase 5: Operations Layer & Human Touchpoint 3.

Kiểm tra:
1. Agent 14: Publisher Agent (Bắn API xuất bản đa kênh Facebook, TikTok, Threads, Shorts).
2. Agent 15: Community Agent (Chiến lược bình luận & điều hướng CTA).
3. Agent 16: Analytics Agent (Học máy phân tích tuần & tự bổ sung Brand Rules mới vào State).
4. Human Touchpoint 3: Điểm duyệt trọn gói Final Package (Text, Video, Cover, Carousel, Threads).
5. Loop Breaker Guard: Cơ chế dừng khẩn cấp khi số chu kỳ vượt quá 4 (total_cycle_count > 4).
6. Toàn trình End-to-End đầy đủ 16 Agent qua 3 điểm ngắt Human Touchpoint.
"""

import pytest
from langgraph.types import Command
from core.state import ContentOSState
from graph.workflow import create_content_os_graph
from agents.operations.publisher_agent import (
    run_publisher_agent,
    publisher_node,
    DefaultPublisherService,
)
from agents.operations.community_agent import run_community_agent, community_node
from agents.operations.analytics_agent import run_analytics_agent, analytics_node


@pytest.fixture
def base_state() -> ContentOSState:
    """State khởi tạo mẫu cho các test cases tầng Operations."""
    return {
        "week_id": "2026-W42",
        "brand_rules": ["Brand voice: Thực chiến, tốc độ, gãy gọn"],
        "trends_feed": [],
        "content_plan": [
            {
                "id": "post_01",
                "angle": "Tự động hóa toàn bộ quy trình sản xuất content với Multi-Agent",
                "hook_concept": "Đừng viết content bằng tay trong năm 2026",
                "target_channel": "Đa kênh",
                "core_message": "Tiết kiệm 80% thời gian với hệ thống 16 Agent",
            }
        ],
        "plan_approved": True,
        "selected_topic": {
            "id": "post_01",
            "angle": "Tự động hóa toàn bộ quy trình sản xuất content với Multi-Agent",
            "hook_concept": "Đừng viết content bằng tay trong năm 2026",
            "target_channel": "Đa kênh",
            "core_message": "Tiết kiệm 80% thời gian với hệ thống 16 Agent",
        },
        "outline": {
            "topic_id": "post_01",
            "hook_variants": ["Hook 1", "Hook 2", "Hook 3"],
            "body_points": ["Điểm 1", "Điểm 2", "Điểm 3"],
            "call_to_action": "Comment 'WORKFLOW' để nhận tài liệu",
        },
        "raw_draft": "Nội dung bài viết Facebook chi tiết về Agentic AI...",
        "draft_score": 9,
        "draft_feedback": "Bài viết đạt chuẩn.",
        "text_revision_count": 0,
        "fact_checked_draft": "Nội dung bài viết Facebook đã kiểm chứng chính tả và số liệu...",
        "threads_posts": [
            "1/ Tự động hóa content không còn là tương lai xa vời.",
            "2/ Dùng 16 AI Agent thay thế các bước thủ công.",
            "3/ Bạn đã thử phương pháp này chưa?",
        ],
        "carousel_slides": [
            {"slide_number": 1, "headline": "Trang 1", "body_content": "Nội dung 1"},
            {"slide_number": 2, "headline": "Trang 2", "body_content": "Nội dung 2"},
            {"slide_number": 3, "headline": "Trang 3", "body_content": "Nội dung 3"},
            {"slide_number": 4, "headline": "Trang 4", "body_content": "Nội dung 4"},
            {"slide_number": 5, "headline": "Trang 5", "body_content": "Nội dung 5"},
        ],
        "video_script": {
            "total_estimated_duration": 45,
            "hook_opening": "Dừng viết content bằng tay lại ngay!",
            "scenes": [],
            "cta_closing": "Comment WORKFLOW ngay!",
        },
        "raw_footage_url": "https://drive.google.com/test_clip.mp4",
        "rendered_video_url": "https://cdn.lintech.vn/videos/clip_rendered_45s.mp4",
        "video_duration": 45,
        "video_approved": True,
        "video_revision_count": 0,
        "cover_image_url": "https://cdn.lintech.vn/images/cover_3x4.jpg",
        "image_approved": True,
        "image_revision_count": 0,
        "final_package_approved": False,
        "user_revision_note": None,
        "total_cycle_count": 1,
        "published_links": {},
        "weekly_metrics": {},
    }


def test_publisher_agent(base_state: ContentOSState):
    """Kiểm tra Agent 14 xuất bản đa kênh (Facebook, TikTok, Threads, YouTube Shorts)."""
    service = DefaultPublisherService(brand_prefix="lintech_test")
    publish_result = run_publisher_agent(base_state, service=service)

    assert publish_result.published_status == "SUCCESS"
    links = publish_result.published_links
    assert "facebook" in links and "facebook.com/lintech_test" in links["facebook"]
    assert "tiktok" in links and "tiktok.com/@lintech_test" in links["tiktok"]
    assert "threads" in links and "threads.net/@lintech_test" in links["threads"]
    assert "youtube_shorts" in links and "youtube.com/shorts" in links["youtube_shorts"]

    # Kiểm tra node
    node_res = publisher_node(base_state)
    assert "published_links" in node_res
    assert len(node_res["published_links"]) == 4


def test_community_agent(base_state: ContentOSState):
    """Kiểm tra Agent 15 sinh chiến lược trả lời bình luận và điều hướng CTA."""
    strategy = run_community_agent(
        base_state["fact_checked_draft"],
        base_state["selected_topic"],
        base_state["brand_rules"],
    )

    assert len(strategy.target_cta_keyword) > 0
    assert len(strategy.seeding_comments) >= 2
    assert len(strategy.faq_replies) >= 2
    assert len(strategy.lead_magnet_url) > 0

    node_res = community_node(base_state)
    assert isinstance(node_res, dict)


def test_analytics_agent_and_brand_rules_update(base_state: ContentOSState):
    """Kiểm tra Agent 16 đo lường hiệu quả và tự bổ sung quy tắc mới vào brand_rules."""
    report = run_analytics_agent(base_state)

    assert len(report.winning_angles) >= 1
    assert len(report.learned_rules) >= 1
    assert "total_impressions" in report.metrics_summary or len(report.metrics_summary) > 0

    node_res = analytics_node(base_state)
    assert "weekly_metrics" in node_res
    assert "brand_rules" in node_res
    assert len(node_res["brand_rules"]) >= 1


def test_full_graph_with_all_three_human_touchpoints(base_state: ContentOSState):
    """Kiểm tra đồ thị chạy xuyên suốt 3 Human Touchpoint và hoàn tất tại END."""
    app = create_content_os_graph()
    thread_config = {"configurable": {"thread_id": "thread_full_e2e_3_touchpoints"}}

    # Khởi tạo state ban đầu sạch
    initial_state = {**base_state}
    initial_state["plan_approved"] = False
    initial_state["raw_footage_url"] = None
    initial_state["final_package_approved"] = False
    initial_state["total_cycle_count"] = 0

    # 1. Chạy tới Human Touchpoint 1 (Duyệt Kế hoạch tuần)
    app.invoke(initial_state, config=thread_config)
    snapshot_1 = app.get_state(thread_config)
    assert "human_approve_plan" in snapshot_1.next

    # 2. Duyệt Plan -> Chạy song song 2 nhánh, nhánh Media dừng tại Touchpoint 2 (Quay Video)
    app.invoke(Command(resume={"approved": True}), config=thread_config)
    snapshot_2 = app.get_state(thread_config)
    assert "human_record_video" in snapshot_2.next

    # 3. User cung cấp link footage thô -> Nhánh Video render & kiểm định, cả 2 nhánh hội tụ tại Touchpoint 3
    user_clip_url = "https://drive.google.com/file/d/clip_raw_1080p/view"
    app.invoke(Command(resume={"raw_footage_url": user_clip_url}), config=thread_config)
    snapshot_3 = app.get_state(thread_config)
    assert "human_approve_final_package" in snapshot_3.next

    # Kiểm tra payload xem trước tại Touchpoint 3
    touchpoint_interrupt = snapshot_3.tasks[0].interrupts[0].value
    assert touchpoint_interrupt["touchpoint"] == 3
    assert touchpoint_interrupt["action"] == "human_approve_final_package"
    assert touchpoint_interrupt["rendered_video_url"] is not None

    # 4. User phê duyệt gói sản phẩm hoàn chỉnh (approved=True) -> Kích hoạt Publisher -> Community -> Analytics -> END
    app.invoke(Command(resume={"approved": True}), config=thread_config)
    final_snapshot = app.get_state(thread_config)
    assert len(final_snapshot.next) == 0  # Đã hoàn thành 100% đồ thị

    final_values = final_snapshot.values
    # Kiểm tra kết quả xuất bản đa kênh
    assert len(final_values["published_links"]) >= 4
    # Kiểm tra kết quả học máy tuần
    assert "metrics_summary" in final_values["weekly_metrics"]
    # Kiểm tra Brand Rules được bổ sung (>= 2 rules nhờ reducer operator.add)
    assert len(final_values["brand_rules"]) >= 2


def test_touchpoint_3_loop_breaker_guard(base_state: ContentOSState):
    """Kiểm tra cơ chế dừng khẩn cấp HALTED khi số chu kỳ vượt quá 4 (total_cycle_count > 4)."""
    from graph.edges import route_after_final_approval

    # Giả lập state đã lặp 5 lần và user vẫn yêu cầu sửa
    state_halted = {**base_state}
    state_halted["final_package_approved"] = False
    state_halted["total_cycle_count"] = 5
    state_halted["user_revision_note"] = "Vẫn chưa ưng ý bài viết."

    route = route_after_final_approval(state_halted)
    from langgraph.graph import END
    assert route == END  # Chuyển trạng thái dừng khẩn cấp
