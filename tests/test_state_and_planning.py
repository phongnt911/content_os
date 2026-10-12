"""Unit tests for Phase 1: ContentOSState, Pydantic Schemas, Research Agent & Planner Agent."""

import pytest
from core.state import (
    ContentOSState,
    TrendTopic,
    ResearchReport,
    ContentPlanItem,
    WeeklyContentPlan,
    OutlineStructure,
    DraftReviewResult,
    FactCheckResult,
    RepurposeThreadsResult,
    CarouselResult,
    VideoScriptResult,
    VideoReviewResult,
    CoverPromptResult,
    ImageReviewResult,
    PublishResult,
    CommentReplyResult,
    AnalyticsReportResult,
)
from agents.planning.research_agent import research_node, run_research_agent
from agents.planning.planner_agent import planner_node, run_planner_agent
import config


def test_content_os_state_structure():
    """Kiểm tra khởi tạo ContentOSState đầy đủ các key theo đặc tả."""
    initial_state: ContentOSState = {
        "week_id": "2026-W42",
        "brand_rules": ["Brand voice: Chuyên gia thân thiện, không dùng thuật ngữ sáo rỗng"],
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

    assert initial_state["week_id"] == "2026-W42"
    assert len(initial_state["brand_rules"]) == 1
    assert initial_state["plan_approved"] is False
    assert initial_state["raw_footage_url"] is None


def test_pydantic_schemas_validation():
    """Kiểm tra tính hợp lệ của tất cả Pydantic Schemas."""
    # Planning schemas
    trend = TrendTopic(
        id="trend_01",
        topic="Multi-Agent Content Creation",
        source_radar="X / Twitter Tech Radar",
        trend_summary="Sự bùng nổ của đồ thị trạng thái LangGraph trong sản xuất video tự động.",
        relevance_score=9.5,
    )
    assert trend.relevance_score == 9.5

    report = ResearchReport(
        trends=[trend],
        summary_insight="Xu hướng tự động hóa đang dẫn đầu",
    )
    assert len(report.trends) == 1

    plan_item = ContentPlanItem(
        id="post_01",
        angle="Góc nhìn thực chiến: 0 đến 100k followers với AI",
        hook_concept="Dừng viết content thủ công nếu bạn không muốn kiệt sức",
        target_channel="Facebook",
        target_audience="Founders & Creators",
        core_message="Quy trình Multi-Agent giúp giảm 80% thời gian sản xuất.",
    )
    assert plan_item.target_channel == "Facebook"

    weekly_plan = WeeklyContentPlan(
        week_id="2026-W42",
        plan_rationale="Chiến lược bao phủ đa kênh",
        items=[plan_item] * 5,
    )
    assert len(weekly_plan.items) == 5

    # Text pipeline schemas
    review = DraftReviewResult(
        draft_score=8,
        draft_feedback="Bài viết mạch lạc, hook cuốn hút.",
        strengths=["Hook tốt", "CTA rõ ràng"],
        improvements=[],
        approved=True,
    )
    assert review.approved is True


def test_config_get_llm():
    """Kiểm tra cơ chế cấp phát LLM instance trong config.py."""
    llm_core = config.get_llm("core")
    llm_fast = config.get_llm("fast")

    assert llm_core is not None
    assert llm_fast is not None


def test_research_agent_execution():
    """Kiểm tra hoạt động của Agent 1 (Research) và node tương thích LangGraph."""
    mock_state: ContentOSState = {
        "week_id": "2026-W42",
        "brand_rules": ["Nội dung chuyên sâu, tôn trọng số liệu"],
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

    result = research_node(mock_state)
    assert "trends_feed" in result
    assert isinstance(result["trends_feed"], list)
    assert len(result["trends_feed"]) > 0

    first_trend = result["trends_feed"][0]
    assert "id" in first_trend
    assert "topic" in first_trend
    assert "trend_summary" in first_trend


def test_planner_agent_execution():
    """Kiểm tra hoạt động của Agent 2 (Planner) với Structured Output."""
    trends = [
        {
            "id": "trend_01",
            "topic": "LangGraph Multi-Agent Architecture",
            "source_radar": "TechCrunch",
            "trend_summary": "Quy trình AI tự hành thay thế viết content thủ công",
            "relevance_score": 9.5,
        }
    ]

    mock_state: ContentOSState = {
        "week_id": "2026-W42",
        "brand_rules": ["Luôn có CTA hướng độc giả dùng thử LinTech Content OS"],
        "trends_feed": trends,
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

    result = planner_node(mock_state)
    assert "content_plan" in result
    assert isinstance(result["content_plan"], list)
    assert 5 <= len(result["content_plan"]) <= 7

    first_post = result["content_plan"][0]
    assert "id" in first_post
    assert "angle" in first_post
    assert "hook_concept" in first_post
    assert "target_channel" in first_post
